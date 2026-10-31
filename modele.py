"""Calculs de l'outil de prévision de la demande d'électricité au Québec.

Ce module ne contient aucune interface : il est utilisé par app.py
et peut être testé séparément.

Principe : la demande moyenne journalière (MW) est modélisée en fonction de la
température par deux droites qui se rejoignent au point T0 ("modèle en V").
T0 est choisi sur 2019-2022 seulement ; l'année 2023 sert uniquement à tester.
"""
import numpy as np
import pandas as pd

CHEMIN_DONNEES = "donnees/journalier.csv"
DEBUT_TEST = "2023-01-01"
VILLES = ["temp_gatineau", "temp_montreal", "temp_quebec"]
NOMS_TEMPERATURE = {
    "Gatineau": "temp_gatineau",
    "Montréal": "temp_montreal",
    "Québec": "temp_quebec",
    "Moyenne des 3 villes": "temp_moyenne3",
}
T0_CANDIDATS = np.arange(5, 25.5, 0.5)       # valeurs de T0 essayées (°C)


# ----------------------------------------------------------------------------
# Données
# ----------------------------------------------------------------------------
def charger_donnees(chemin=CHEMIN_DONNEES):
    """Lit le tableau journalier et garde les jours utilisables.

    On retire les journées dont des heures de demande manquent, et les jours où
    une des trois villes n'a pas de température, pour comparer tous les modèles
    sur exactement les mêmes jours.
    """
    j = pd.read_csv(chemin, parse_dates=["jour"])
    j = j[~j["jour_incomplet"]].copy()
    j["temp_moyenne3"] = j[VILLES].mean(axis=1)          # moyenne simple des trois villes
    return j.dropna(subset=VILLES).reset_index(drop=True)


def decouper(j):
    """Entraînement = avant 2023 ; test = 2023."""
    return j[j["jour"] < DEBUT_TEST].copy(), j[j["jour"] >= DEBUT_TEST].copy()


# ----------------------------------------------------------------------------
# Petits outils de calcul
# ----------------------------------------------------------------------------
def ajuster(X, y):
    """Régression linéaire par moindres carrés (avec constante). Renvoie les coefficients."""
    X1 = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return beta


def predire(X, beta):
    return np.column_stack([np.ones(len(X)), X]) @ beta


def colonnes_v(T, t0):
    """Degrés sous T0 et degrés au-dessus de T0 (0 de l'autre côté)."""
    return np.column_stack([np.maximum(t0 - T, 0), np.maximum(T - t0, 0)])


def indicateurs_jour(df):
    """6 colonnes 0/1 : lundi ... samedi (le dimanche sert de référence)."""
    return (df["jour_semaine"].to_numpy()[:, None] == np.arange(6)).astype(float)


def _matrice(df, colonne, t0, avec_jours):
    X = colonnes_v(df[colonne].to_numpy(), t0)
    if avec_jours:
        X = np.column_stack([X, indicateurs_jour(df)])
    return X


def mesures(y, yhat):
    """MAE et RMSE en MW, MAPE en %."""
    err = np.asarray(y) - np.asarray(yhat)
    return {
        "MAE": float(np.abs(err).mean()),
        "RMSE": float(np.sqrt((err ** 2).mean())),
        "MAPE": float((np.abs(err) / np.asarray(y)).mean() * 100),
    }


# ----------------------------------------------------------------------------
# Modèle
# ----------------------------------------------------------------------------
def entrainer(train, colonne, avec_jours):
    """Choisit T0 (le meilleur ajustement sur l'entraînement) et ajuste le modèle."""
    y = train["mw_moyen"].to_numpy()
    meilleur = None
    for t0 in T0_CANDIDATS:
        X = _matrice(train, colonne, t0, avec_jours)
        beta = ajuster(X, y)
        sse = ((y - predire(X, beta)) ** 2).sum()        # erreur quadratique totale
        if meilleur is None or sse < meilleur[0]:
            meilleur = (sse, t0, beta)
    _, t0, beta = meilleur
    return {"colonne": colonne, "avec_jours": avec_jours, "t0": float(t0), "beta": beta}


def prevoir(modele, df):
    """Demande moyenne journalière prévue (MW) pour chaque ligne de df."""
    X = _matrice(df, modele["colonne"], modele["t0"], modele["avec_jours"])
    return predire(X, modele["beta"])


def references(train, test):
    """Deux références simples à battre.

    Référence 1 : toujours la moyenne de l'entraînement.
    Référence 2 : moyenne de l'entraînement pour le même mois et le même type de jour
                  (semaine ou fin de semaine).
    """
    ref1 = np.full(len(test), train["mw_moyen"].mean())
    tr = train.assign(mois=train["jour"].dt.month, fds=train["jour_semaine"] >= 5)
    moy = tr.groupby(["mois", "fds"])["mw_moyen"].mean()
    cles = zip(test["jour"].dt.month, test["jour_semaine"] >= 5)
    ref2 = np.array([moy[(mois, fds)] for mois, fds in cles])
    return ref1, ref2


def comparer_modeles(train, test):
    """Tableau des 8 modèles (4 définitions de température, avec ou sans jours de la semaine)."""
    y = test["mw_moyen"].to_numpy()
    lignes = []
    for nom, colonne in NOMS_TEMPERATURE.items():
        for avec_jours in (False, True):
            mod = entrainer(train, colonne, avec_jours)
            mes = mesures(y, prevoir(mod, test))
            lignes.append({
                "Température": nom,
                "Jours de la semaine": "oui" if avec_jours else "non",
                "T0 (°C)": mod["t0"],
                "MAE (MW)": round(mes["MAE"]),
                "RMSE (MW)": round(mes["RMSE"]),
                "MAPE (%)": round(mes["MAPE"], 2),
            })
    return pd.DataFrame(lignes)


# ----------------------------------------------------------------------------
# Prévision à 7 jours et sensibilité à l'imprécision de la température
# ----------------------------------------------------------------------------
def intervalle_erreur(modele, test, niveau=0.90):
    """Erreurs (réel - prévu) observées sur l'année de test, pour borner une prévision.

    Renvoie (erreur_basse, erreur_haute) : les quantiles de ces erreurs qui encadrent
    une proportion `niveau` des jours de test. L'erreur basse est en général négative.
    """
    y = test["mw_moyen"].to_numpy()
    erreurs = y - prevoir(modele, test)
    alpha = (1 - niveau) / 2
    return float(np.quantile(erreurs, alpha)), float(np.quantile(erreurs, 1 - alpha))


def prevoir_semaine(modele, date_debut, temperatures, niveau=0.90, test=None):
    """Demande prévue (MW) pour des jours consécutifs, à partir de températures saisies.

    La température saisie doit correspondre à la définition utilisée par le modèle
    (une ville, ou la moyenne des trois villes). Si `test` est fourni, on ajoute un
    intervalle (colonnes `bas` et `haut`) fondé sur les erreurs observées sur `test`.
    """
    jours = pd.date_range(pd.Timestamp(date_debut), periods=len(temperatures))
    df = pd.DataFrame({
        "jour": jours,
        "jour_semaine": jours.dayofweek,
        modele["colonne"]: np.asarray(temperatures, dtype=float),
    })
    df["prevision_mw"] = prevoir(modele, df)
    if test is not None:
        bas, haut = intervalle_erreur(modele, test, niveau)
        df["bas"] = df["prevision_mw"] + bas
        df["haut"] = df["prevision_mw"] + haut
    return df


def sensibilite_bruit(modele, test, ecarts_types=(0, 1, 2, 3, 4), n_tirages=200, graine=42):
    """Simule une température imprécise : on ajoute un bruit aléatoire (loi normale,
    écart-type en °C) aux températures de test, sans ré-entraîner le modèle, et on
    mesure la MAE. Chaque niveau de bruit est répété `n_tirages` fois."""
    rng = np.random.default_rng(graine)
    y = test["mw_moyen"].to_numpy()
    colonne = modele["colonne"]
    lignes = []
    mae_sans_bruit = None
    for sd in ecarts_types:
        maes = []
        for _ in range(1 if sd == 0 else n_tirages):
            t = test.copy()
            if sd > 0:
                t[colonne] = t[colonne].to_numpy() + rng.normal(0, sd, len(t))
            maes.append(mesures(y, prevoir(modele, t))["MAE"])
        maes = np.array(maes)
        moyenne = float(maes.mean())
        if mae_sans_bruit is None:
            mae_sans_bruit = moyenne
        lignes.append({
            "Bruit sur la température (écart-type, °C)": sd,
            "MAE moyenne (MW)": round(moyenne),
            "MAE, 5e centile (MW)": round(float(np.quantile(maes, 0.05))),
            "MAE, 95e centile (MW)": round(float(np.quantile(maes, 0.95))),
            "Hausse par rapport à 0 °C (%)": round((moyenne / mae_sans_bruit - 1) * 100, 1),
        })
    return pd.DataFrame(lignes)
