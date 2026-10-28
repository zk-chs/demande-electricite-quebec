import glob
import pandas as pd

# 1) Lire les 15 fichiers et les empiler dans un seul tableau
morceaux = []
for f in sorted(glob.glob("donnees/meteo_*.csv")):
    d = pd.read_csv(f)
    d["ville"] = f.split("meteo_")[1].split("_")[0]
    morceaux.append(d)
meteo = pd.concat(morceaux, ignore_index=True)
meteo["date"] = pd.to_datetime(meteo["Date/Time"])

# 2) Tableau : une ligne par date, une colonne par ville
temp = meteo.pivot(index="date", columns="ville", values="Mean Temp (°C)")
print("Nombre de jours :", len(temp))

# 3) Pour chaque jour, combien de villes n'ont pas de température ?
nb_manquantes = temp.isna().sum(axis=1)
print("\nNombre de jours selon le nombre de villes sans température :")
print(nb_manquantes.value_counts().sort_index())

print("\nJours où au moins 2 villes manquent :")
print(temp[nb_manquantes >= 2])

# 4) Plus longue série de jours manquants consécutifs, par ville
print()
for ville in temp.columns:
    manquant = temp[ville].isna()
    groupe = (manquant != manquant.shift()).cumsum()
    plus_longue = manquant.groupby(groupe).sum().max()
    print(ville, "| plus longue série de jours manquants :", int(plus_longue))
