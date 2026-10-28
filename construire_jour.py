import glob
import pandas as pd

# 1) Demande horaire : empiler les 5 années (avec la correction de la date de 2021)
morceaux = []
for annee in range(2019, 2024):
    d = pd.read_excel(f"donnees/demande_{annee}.xlsx")
    d.columns = ["date", "mw"]
    if annee == 2021:
        d.loc[d.index[-1], "date"] = pd.Timestamp("2022-01-01 00:00")
    morceaux.append(d)
dem = pd.concat(morceaux, ignore_index=True)

# 2) Journée = date de l'heure qui COMMENCE (l'étiquette 00:00 appartient au jour précédent)
dem["jour"] = (dem["date"] - pd.Timedelta(hours=1)).dt.normalize()

# 3) Une ligne par jour
par_jour = dem.groupby("jour").agg(
    n_lignes=("mw", "size"),            # heures présentes dans le fichier (23, 24 ou 25)
    n_valides=("mw", "count"),          # heures avec une valeur (count ignore les vides)
    mw_moyen=("mw", "mean"),            # demande moyenne de la journée (MW), heures valides seulement
    mwh_total=("mw", lambda s: s.sum(min_count=1)),   # total du jour (MWh) ; vide si aucune heure valide
)
par_jour["jour_incomplet"] = par_jour["n_valides"] < par_jour["n_lignes"]

# 4) Météo : une colonne de température moyenne par ville
m = []
for f in glob.glob("donnees/meteo_*.csv"):
    t = pd.read_csv(f)
    t["ville"] = f.split("meteo_")[1].split("_")[0]
    m.append(t)
meteo = pd.concat(m)
meteo["jour"] = pd.to_datetime(meteo["Date/Time"])
temp = meteo.pivot(index="jour", columns="ville", values="Mean Temp (°C)")
temp.columns = ["temp_" + c for c in temp.columns]

# 5) Fusion au jour près
jour = par_jour.join(temp, how="outer")
jour["jour_semaine"] = jour.index.dayofweek          # 0 = lundi ... 6 = dimanche
jour.index.name = "jour"
jour.to_csv("donnees/journalier.csv")

# 6) Résumé
print("Jours :", len(jour), "| du", jour.index.min().date(), "au", jour.index.max().date())
print("\nNombre de lignes horaires par jour (23 = printemps, 25 = automne) :")
print(jour["n_lignes"].value_counts().sort_index().to_string())
print("\nJours avec des heures manquantes :")
print(jour[jour["jour_incomplet"]][["n_lignes", "n_valides"]].to_string())
print("\nJours sans température, par ville :")
print(jour[["temp_gatineau", "temp_montreal", "temp_quebec"]].isna().sum().to_string())
print("\nAperçu :")
print(jour.head(3).to_string())
