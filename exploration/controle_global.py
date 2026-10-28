import pandas as pd

# 1) Empiler les 5 années
morceaux = []
for annee in range(2019, 2024):
    d = pd.read_excel(f"donnees/demande_{annee}.xlsx")
    d.columns = ["date", "mw"]
    if annee == 2021:
        # correction documentée : la dernière ligne porte 2023-01-01 au lieu de 2022-01-01
        d.loc[d.index[-1], "date"] = pd.Timestamp("2022-01-01 00:00")
    morceaux.append(d)
dem = pd.concat(morceaux, ignore_index=True)
print("Lignes au total :", len(dem), "| première :", dem["date"].iloc[0], "| dernière :", dem["date"].iloc[-1])

# 2) Continuité : combien d'écarts différents d'une heure ?
ecart = dem["date"].diff()
bizarres = dem[(ecart != pd.Timedelta(hours=1)) & ecart.notna()].copy()
bizarres["ecart"] = ecart[bizarres.index]
print("\nÉcarts différents d'une heure :", len(bizarres), "(on attend 10 : 5 printemps + 5 automnes)")
print(bizarres.to_string())

# 3) Valeurs extrêmes
print("\n10 plus petites valeurs :")
print(dem.nsmallest(10, "mw").to_string())
print("\n10 plus grandes valeurs :")
print(dem.nlargest(10, "mw").to_string())

# 4) Plus grands sauts d'une heure à l'autre
dem["saut"] = dem["mw"].diff().abs()
print("\n10 plus grands sauts d'une heure à l'autre (MW) :")
print(dem.nlargest(10, "saut").to_string())
