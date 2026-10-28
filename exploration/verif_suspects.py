import glob
import pandas as pd

# Demande empilée, avec la correction de la date de 2021
morceaux = []
for annee in range(2019, 2024):
    d = pd.read_excel(f"donnees/demande_{annee}.xlsx")
    d.columns = ["date", "mw"]
    if annee == 2021:
        d.loc[d.index[-1], "date"] = pd.Timestamp("2022-01-01 00:00")
    morceaux.append(d)
dem = pd.concat(morceaux, ignore_index=True)

# 1) Fenêtre de 8 lignes autour de chaque moment suspect
for ts in ["2019-05-08 03:00", "2019-11-11 19:00", "2022-10-25 23:00", "2019-10-03 23:00"]:
    i = dem.index[dem["date"] == pd.Timestamp(ts)][0]
    print("=====", ts)
    print(dem.iloc[i - 4: i + 4].to_string())

# 2) Températures moyennes des journées de pointe, dans les trois villes
m = []
for f in glob.glob("donnees/meteo_*.csv"):
    t = pd.read_csv(f)
    t["ville"] = f.split("meteo_")[1].split("_")[0]
    m.append(t)
meteo = pd.concat(m)
meteo["date"] = pd.to_datetime(meteo["Date/Time"])
temp = meteo.pivot(index="date", columns="ville", values="Mean Temp (°C)")
print("\n===== Températures moyennes (°C) des journées de forte demande")
print(temp.loc[["2022-01-21", "2022-01-27", "2023-02-03", "2023-02-04"]].to_string())
print("\nTempérature la plus basse de la période, par ville :")
print(temp.min().to_string())
