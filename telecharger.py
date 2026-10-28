import os
import requests

os.makedirs("donnees", exist_ok=True)

# 1) Demande Hydro-Québec, 2019 à 2023
for annee in range(2019, 2024):
    url = ("https://www.hydroquebec.com/data/documents-donnees/donnees-ouvertes/"
           f"xlsx/historique-demande/{annee}-demande-electricite-quebec.xlsx")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with open(f"donnees/demande_{annee}.xlsx", "wb") as f:
        f.write(r.content)
    print("Téléchargé :", annee)

# 2) Météo quotidienne : un fichier par station et par année
STATIONS = {"montreal": 30165, "quebec": 26892, "gatineau": 53001}

for nom, sid in STATIONS.items():
    if sid is None:
        print("Numéro manquant pour la station :", nom)
        continue
    for annee in range(2019, 2024):
        url = ("https://climate.weather.gc.ca/climate_data/bulk_data_e.html"
               f"?format=csv&stationID={sid}&Year={annee}&Month=1&Day=1"
               "&timeframe=2&submit=Download+Data")
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        with open(f"donnees/meteo_{nom}_{annee}.csv", "wb") as f:
            f.write(r.content)
        print("Téléchargé :", nom, annee)
