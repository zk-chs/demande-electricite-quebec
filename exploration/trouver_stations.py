import pandas as pd

url = ("https://collaboration.cmc.ec.gc.ca/cmc/climate/"
       "Get_More_Data_Plus_de_donnees/Station%20Inventory%20EN.csv")
inv = pd.read_csv(url, skiprows=3)
print("COLONNES :", inv.columns.tolist())

for mot in ["TRUDEAU", "JEAN LESAGE", "GATINEAU"]:
    sel = inv[inv["Name"].str.contains(mot, case=False, na=False)]
    print("=====", mot)
    print(sel.to_string())
