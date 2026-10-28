"""Application Streamlit : demande d'électricité au Québec selon la température.

Lancement :  streamlit run app.py
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

import modele as m

st.set_page_config(page_title="Demande d'électricité au Québec", layout="wide")


# Les calculs lourds sont mis en cache : ils ne sont refaits que si les paramètres changent
@st.cache_data
def charger():
    return m.charger_donnees()


@st.cache_data
def entrainer(colonne, avec_jours):
    train, _ = m.decouper(charger())
    return m.entrainer(train, colonne, avec_jours)


@st.cache_data
def tableau_modeles():
    train, test = m.decouper(charger())
    return m.comparer_modeles(train, test)


# ---------------------------------------------------------------- Barre latérale
j = charger()
train, test = m.decouper(j)

st.sidebar.title("Paramètres")
page = st.sidebar.radio("Page", ["Température et demande", "Fiabilité du modèle"])
nom_temp = st.sidebar.selectbox("Température utilisée", list(m.NOMS_TEMPERATURE.keys()), index=3)
colonne = m.NOMS_TEMPERATURE[nom_temp]
avec_jours = st.sidebar.checkbox("Tenir compte des jours de la semaine", value=True)
st.sidebar.caption(
    "Sources : demande horaire d'Hydro-Québec (CC BY-NC 4.0) ; "
    "températures quotidiennes d'Environnement Canada."
)
st.sidebar.caption(
    f"{len(train)} jours d'entraînement (2019-2022), {len(test)} jours de test (2023)."
)

st.title("Demande d'électricité au Québec")

# ---------------------------------------------------------------- Page 1
if page == "Température et demande":
    st.header("Relation entre la température et la demande")
    st.caption(
        "Chaque point est une journée. Le modèle en V est ajusté sur 2019-2022 "
        "(deux droites qui se rejoignent au point T0). "
        "Il ne tient pas compte des jours de la semaine sur ce graphique."
    )
    mod_v = entrainer(colonne, False)
    t0, b = mod_v["t0"], mod_v["beta"]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(train[colonne], train["mw_moyen"], s=10, alpha=0.4, label="Entraînement (2019-2022)")
    ax.scatter(test[colonne], test["mw_moyen"], s=10, alpha=0.6, color="tab:orange", label="Test (2023)")
    xs = np.linspace(j[colonne].min(), j[colonne].max(), 200)
    ax.plot(xs, b[0] + b[1] * np.maximum(t0 - xs, 0) + b[2] * np.maximum(xs - t0, 0),
            color="black", lw=2, label=f"Modèle en V (T0 = {t0:.1f} °C)")
    ax.axvline(t0, ls="--", color="gray")
    ax.set_xlabel(f"Température moyenne du jour, {nom_temp} (°C)")
    ax.set_ylabel("Demande moyenne journalière (MW)")
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Point de jonction T0", f"{t0:.1f} °C")
    c2.metric("Demande minimale estimée", f"{b[0]:,.0f} MW".replace(",", " "))
    c3.metric("Pente côté froid (MW par °C)", f"{b[1]:,.0f}".replace(",", " "))
    c4.metric("Pente côté chaud (MW par °C)", f"{b[2]:,.0f}".replace(",", " "))

# ---------------------------------------------------------------- Page 2
else:
    st.header("Fiabilité du modèle")
    st.caption(
        "Le modèle est entraîné sur 2019-2022 puis évalué sur 2023, une année qu'il n'a pas "
        "utilisée pour choisir T0 ni pour ajuster ses coefficients."
    )
    modele = entrainer(colonne, avec_jours)
    y = test["mw_moyen"].to_numpy()
    yhat = m.prevoir(modele, test)
    ref1, ref2 = m.references(train, test)

    mes = m.mesures(y, yhat)
    mes1 = m.mesures(y, ref1)
    mes2 = m.mesures(y, ref2)

    c1, c2, c3 = st.columns(3)
    c1.metric("MAE (erreur absolue moyenne)", f"{mes['MAE']:.0f} MW")
    c2.metric("RMSE", f"{mes['RMSE']:.0f} MW")
    c3.metric("MAPE (erreur en % de la demande)", f"{mes['MAPE']:.2f} %")

    st.subheader("Comparaison avec deux références simples")
    tab = pd.DataFrame([
        {"Modèle": f"Modèle choisi ({nom_temp}, jours de la semaine : {'oui' if avec_jours else 'non'})", **mes},
        {"Modèle": "Référence 1 : moyenne de 2019-2022", **mes1},
        {"Modèle": "Référence 2 : moyenne du même mois et du même type de jour", **mes2},
    ]).rename(columns={"MAE": "MAE (MW)", "RMSE": "RMSE (MW)", "MAPE": "MAPE (%)"})
    tab["MAE (MW)"] = tab["MAE (MW)"].round(0)
    tab["RMSE (MW)"] = tab["RMSE (MW)"].round(0)
    tab["MAPE (%)"] = tab["MAPE (%)"].round(2)
    st.dataframe(tab, hide_index=True)

    g1, g2 = st.columns(2)
    g1.metric("Réduction de la MAE par rapport à la référence 1",
              f"{(mes1['MAE'] - mes['MAE']) / mes1['MAE'] * 100:.1f} %")
    g2.metric("Réduction de la MAE par rapport à la référence 2",
              f"{(mes2['MAE'] - mes['MAE']) / mes2['MAE'] * 100:.1f} %")

    st.subheader("Demande réelle et demande prévue en 2023")
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(test["jour"], y, label="Réelle", lw=1.2)
    ax.plot(test["jour"], yhat, label="Prévue par le modèle", lw=1.2, color="tab:orange")
    ax.set_ylabel("Demande moyenne journalière (MW)")
    ax.legend()
    fig.autofmt_xdate()
    st.pyplot(fig)
    plt.close(fig)

    with st.expander("Définition des mesures d'erreur"):
        st.markdown(
            "- **MAE** : moyenne des écarts absolus entre la demande réelle et la demande prévue, en MW.\n"
            "- **RMSE** : racine de la moyenne des écarts élevés au carré, en MW ; elle pèse davantage les grosses erreurs.\n"
            "- **MAPE** : moyenne des écarts absolus exprimés en pourcentage de la demande réelle."
        )
    with st.expander("Comparaison des 8 modèles sur 2023"):
        st.dataframe(tableau_modeles(), hide_index=True)
