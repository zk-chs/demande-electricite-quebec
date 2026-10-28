import numpy as np
import pandas as pd

j = pd.read_csv("donnees/journalier.csv", parse_dates=["jour"])
j = j[~j["jour_incomplet"]]          # exploration : journées incomplètes écartées


def r2(X, y):
    # régression linéaire par moindres carrés ; renvoie R² et les coefficients
    X1 = np.column_stack([np.ones(len(y)), X])      # colonne de 1 = constante
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    sse = ((y - X1 @ beta) ** 2).sum()              # erreur résiduelle
    sst = ((y - y.mean()) ** 2).sum()               # variabilité totale
    return 1 - sse / sst, beta


for v in ["gatineau", "montreal", "quebec"]:
    d = j[[f"temp_{v}", "mw_moyen"]].dropna()
    T = d[f"temp_{v}"].to_numpy()
    y = d["mw_moyen"].to_numpy()

    # 1) Une seule droite
    r2_droite, b = r2(T.reshape(-1, 1), y)

    # 2) Deux droites qui se rejoignent en T0 (on essaie T0 de 5 à 25 °C)
    meilleur = None
    for t0 in np.arange(5, 25.5, 0.5):
        X = np.column_stack([np.maximum(t0 - T, 0), np.maximum(T - t0, 0)])
        val, beta = r2(X, y)
        if meilleur is None or val > meilleur[0]:
            meilleur = (val, t0, beta)
    val, t0, beta = meilleur

    print("=====", v, "| jours :", len(d))
    print(f"Une droite  : R² = {r2_droite:.3f} | pente = {b[1]:.0f} MW par °C")
    print(f"Deux droites: R² = {val:.3f} | T0 = {t0:.1f} °C | minimum = {beta[0]:.0f} MW")
    print(f"   côté froid : {beta[1]:.0f} MW par °C sous T0 ; côté chaud : {beta[2]:.0f} MW par °C au-dessus de T0")
    print()
