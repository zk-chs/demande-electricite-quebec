import pandas as pd

df = pd.read_excel("donnees/demande_2019.xlsx")
df.columns = ["date", "mw"]

vides = df[df["mw"].isna()].copy()
print("Heures sans valeur :", len(vides))
print(vides.to_string())

# Regrouper par jour : on recule d'une heure, car l'étiquette 00:00 appartient au jour précédent
vides["jour"] = (vides["date"] - pd.Timedelta(hours=1)).dt.date
print()
print("Nombre d'heures manquantes par jour :")
print(vides.groupby("jour").size())
