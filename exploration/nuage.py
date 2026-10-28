import os
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("figures", exist_ok=True)

j = pd.read_csv("donnees/journalier.csv", parse_dates=["jour"])
j = j[~j["jour_incomplet"]]          # exploration : on met de côté les 4 journées incomplètes
villes = ["gatineau", "montreal", "quebec"]

fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
for ax, v in zip(axes, villes):
    ax.scatter(j[f"temp_{v}"], j["mw_moyen"], s=8, alpha=0.4)
    ax.set_title(v.capitalize())
    ax.set_xlabel("Température moyenne du jour (°C)")
axes[0].set_ylabel("Demande moyenne (MW)")
plt.tight_layout()
plt.savefig("figures/nuage_demande_temperature.png", dpi=150)
print("Image enregistrée : figures/nuage_demande_temperature.png\n")

for v in villes:
    r = j[f"temp_{v}"].corr(j["mw_moyen"])
    print("=====", v, "| r de Pearson =", round(r, 3))
    tranches = pd.cut(j[f"temp_{v}"], bins=range(-35, 45, 5))
    print(j.groupby(tranches, observed=True)["mw_moyen"].agg(["count", "mean"]).round(0).to_string())
    print()
