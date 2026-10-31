"""Effet d'une température imprécise sur l'erreur du modèle (simulation).

Lancement :  python3 tester_imprecision.py
"""
import modele as m

j = m.charger_donnees()
train, test = m.decouper(j)

for nom, colonne in m.NOMS_TEMPERATURE.items():
    for avec_jours in (False, True):
        mod = m.entrainer(train, colonne, avec_jours)
        print(f"===== Température : {nom} | jours de la semaine : {'oui' if avec_jours else 'non'}")
        print(m.sensibilite_bruit(mod, test).to_string(index=False))
        print()

y = test["mw_moyen"].to_numpy()
ref1, ref2 = m.references(train, test)
print("Rappel des références (MAE sur 2023) :",
      f"référence 1 = {m.mesures(y, ref1)['MAE']:.0f} MW ; référence 2 = {m.mesures(y, ref2)['MAE']:.0f} MW")
