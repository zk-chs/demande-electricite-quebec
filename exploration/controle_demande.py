import pandas as pd

lignes = []
for annee in range(2019, 2024):
    df = pd.read_excel(f"donnees/demande_{annee}.xlsx")
    df.columns = ["date", "mw"]

    ecart = df["date"].diff()                       # temps écoulé depuis la ligne précédente
    irreguliers = df[(ecart != pd.Timedelta(hours=1)) & ecart.notna()].copy()
    irreguliers["ecart"] = ecart[irreguliers.index]

    lignes.append({
        "annee": annee,
        "lignes": len(df),
        "premiere": df["date"].iloc[0],
        "derniere": df["date"].iloc[-1],
        "dates_en_double": int(df["date"].duplicated().sum()),
        "ecarts_pas_1h": len(irreguliers),
        "mw_manquants": int(df["mw"].isna().sum()),
        "mw_min": df["mw"].min(),
        "mw_max": df["mw"].max(),
    })
    if len(irreguliers) > 0:
        print("--- écarts irréguliers dans", annee)
        print(irreguliers.to_string())

print()
print(pd.DataFrame(lignes).to_string(index=False))
