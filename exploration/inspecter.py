import pandas as pd

for annee in range(2019, 2024):
    chemin = f"donnees/demande_{annee}.xlsx"
    xl = pd.ExcelFile(chemin)
    print("=====", annee, "| feuilles :", xl.sheet_names)
    df = xl.parse(xl.sheet_names[0])
    print("Forme (lignes, colonnes) :", df.shape)
    print("Colonnes :", list(df.columns))
    print(df.head(3))
    print(df.tail(3))
