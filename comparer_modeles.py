import numpy as np
import pandas as pd

# 1) Données : on garde les jours complets et les jours où les 3 villes ont une température,
#    pour que tous les modèles soient comparés sur exactement les mêmes jours
j = pd.read_csv("donnees/journalier.csv", parse_dates=["jour"])
j = j[~j["jour_incomplet"]].copy()
villes = ["temp_gatineau", "temp_montreal", "temp_quebec"]
j["temp_moyenne3"] = j[villes].mean(axis=1)       # moyenne simple des trois villes
j = j.dropna(subset=villes)

# 2) Découpage dans le temps : entraînement = 2019 à 2022, test = 2023 (jamais utilisée pour choisir quoi que ce soit)
train = j[j["jour"] < "2023-01-01"]
test = j[j["jour"] >= "2023-01-01"]
print("Jours d'entraînement :", len(train), "| jours de test :", len(test))


# 3) Petits outils
def ajuster(X, y):
    X1 = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return beta

def predire(X, beta):
    return np.column_stack([np.ones(len(X)), X]) @ beta

def colonnes_V(T, t0):
    return np.column_stack([np.maximum(t0 - T, 0), np.maximum(T - t0, 0)])

def indicateurs_jour(df):
    # 6 colonnes 0/1 : lundi ... samedi (le dimanche sert de référence)
    return (df["jour_semaine"].to_numpy()[:, None] == np.arange(6)).astype(float)

def mesures(y, yhat):
    err = y - yhat
    return np.abs(err).mean(), np.sqrt((err ** 2).mean()), (np.abs(err) / y).mean() * 100


# 4) Chaque modèle : T0 choisi sur l'entraînement seulement, puis évaluation sur 2023
ytr = train["mw_moyen"].to_numpy()
yte = test["mw_moyen"].to_numpy()
lignes = []
for nom, col in [("Gatineau", "temp_gatineau"), ("Montréal", "temp_montreal"),
                 ("Québec", "temp_quebec"), ("Moyenne des 3 villes", "temp_moyenne3")]:
    for avec_jours in [False, True]:
        Ttr = train[col].to_numpy()
        Tte = test[col].to_numpy()
        meilleur = None
        for t0 in np.arange(5, 25.5, 0.5):
            Xtr = colonnes_V(Ttr, t0)
            if avec_jours:
                Xtr = np.column_stack([Xtr, indicateurs_jour(train)])
            beta = ajuster(Xtr, ytr)
            sse = ((ytr - predire(Xtr, beta)) ** 2).sum()
            if meilleur is None or sse < meilleur[0]:
                meilleur = (sse, t0, beta)
        _, t0, beta = meilleur
        Xte = colonnes_V(Tte, t0)
        if avec_jours:
            Xte = np.column_stack([Xte, indicateurs_jour(test)])
        mae, rmse, mape = mesures(yte, predire(Xte, beta))
        lignes.append({"Température": nom, "Jours de la semaine": "oui" if avec_jours else "non",
                       "T0 (°C)": t0, "MAE (MW)": round(mae), "RMSE (MW)": round(rmse), "MAPE (%)": round(mape, 2)})

resultats = pd.DataFrame(lignes)
print("\nÉvaluation sur 2023 (modèle en V, T0 choisi sur 2019-2022) :")
print(resultats.to_string(index=False))

# 5) Références simples (à battre)
mae, rmse, mape = mesures(yte, np.full(len(yte), ytr.mean()))
print(f"\nRéférence 1, toujours la moyenne de 2019-2022 : MAE = {mae:.0f} | RMSE = {rmse:.0f} | MAPE = {mape:.2f} %")

train2 = train.assign(mois=train["jour"].dt.month, fds=(train["jour_semaine"] >= 5))
test2 = test.assign(mois=test["jour"].dt.month, fds=(test["jour_semaine"] >= 5))
moy = train2.groupby(["mois", "fds"])["mw_moyen"].mean()
yhat = test2.apply(lambda r: moy[(r["mois"], r["fds"])], axis=1).to_numpy()
mae, rmse, mape = mesures(yte, yhat)
print(f"Référence 2, moyenne du même mois et du même type de jour : MAE = {mae:.0f} | RMSE = {rmse:.0f} | MAPE = {mape:.2f} %")

# --- Écarts calculés pour aider à lire le tableau (les conclusions restent à rédiger) ---
tab = resultats.pivot(index="Température", columns="Jours de la semaine", values="MAE (MW)")
tab["Gain des jours de la semaine (MW)"] = tab["non"] - tab["oui"]
tab["Gain (%)"] = (tab["Gain des jours de la semaine (MW)"] / tab["non"] * 100).round(1)
print("\nEffet des jours de la semaine, par définition de température :")
print(tab.to_string())

sans = resultats[resultats["Jours de la semaine"] == "non"]["MAE (MW)"]
print("\nSans jours de la semaine : plus petite MAE =", sans.min(), "| plus grande MAE =", sans.max(),
      "| écart =", sans.max() - sans.min(), "MW (", round((sans.max() - sans.min()) / sans.max() * 100, 1), "% )")

meilleur = resultats["MAE (MW)"].min()
ref1 = np.abs(yte - ytr.mean()).mean()
ref2 = np.abs(yte - yhat).mean()
print("\nMeilleur modèle : MAE =", meilleur)
print(f"Contre la référence 1 : gain = {ref1 - meilleur:.0f} MW ({(ref1 - meilleur) / ref1 * 100:.1f} %)")
print(f"Contre la référence 2 : gain = {ref2 - meilleur:.0f} MW ({(ref2 - meilleur) / ref2 * 100:.1f} %)")
