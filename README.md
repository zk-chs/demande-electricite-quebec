# Demande d'électricité au Québec : modèle selon la température

Application développée dans le cadre du projet de session du cours INF-5103
(Concepts statistiques pour la science des données), Université du Québec en
Outaouais, automne 2026.

## Objet

Outil d'aide à la planification destiné à une équipe d'exploitation de réseau
électrique. Il modélise la demande moyenne journalière d'électricité au Québec
(en MW) en fonction de la température et du jour de la semaine, et permet
d'évaluer la fiabilité du modèle sur une année de test.

## Fonctionnalités

- Page « Température et demande » : nuage de points de la demande en fonction de
  la température, courbe du modèle en V (deux droites qui se rejoignent au point
  T0), indicateurs du modèle.
- Page « Fiabilité du modèle » : erreurs (MAE, RMSE, MAPE) sur 2023, comparaison
  avec deux références simples, demande réelle et prévue, tableau des 8 modèles.
- Barre latérale : choix de la température (Gatineau, Montréal, Québec ou
  moyenne des trois villes) et prise en compte ou non des jours de la semaine.

## Lancer l'application

Prérequis : Python 3.12 et un accès Internet pour l'installation.

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Commande unique de lancement :

    streamlit run app.py

L'application s'ouvre dans le navigateur à l'adresse http://localhost:8501.
Au premier lancement, Streamlit peut demander une adresse courriel : appuyer
simplement sur Entrée. Sous Windows, l'activation de l'environnement se fait
avec `.venv\Scripts\activate`.

## Données

Le fichier `donnees/journalier.csv` est fourni avec le dépôt : une ligne par jour,
du 1er janvier 2019 au 31 décembre 2023 (1826 jours).

Sources :

- Demande horaire : Hydro-Québec, historique de la demande d'électricité au
  Québec (données ouvertes, licence CC BY-NC 4.0).
  https://www.hydroquebec.com/documents-data/open-data/history-electricity-demand-quebec/
- Températures quotidiennes : Environnement et Changement climatique Canada,
  stations Montréal/Pierre Elliott Trudeau Intl (30165), Québec/Jean Lesage Intl
  (26892) et Ottawa Gatineau A (53001). Licence : [à vérifier].

Données récupérées le 26 octobre 2026. Pour les reconstituer :

    python3 telecharger.py
    python3 construire_jour.py

## Méthode, en résumé

La demande moyenne journalière est modélisée par deux droites de la température
qui se rejoignent en T0. T0 et les coefficients sont choisis sur 2019-2022 ;
l'année 2023 sert uniquement de test. Les modèles sont comparés à deux
références : la moyenne de 2019-2022, et la moyenne du même mois et du même type
de jour.

## Contenu du dépôt

- `app.py` : interface Streamlit.
- `modele.py` : calculs (chargement, modèle, mesures d'erreur).
- `telecharger.py`, `construire_jour.py` : récupération et préparation des données.
- `comparer_modeles.py` : comparaison des modèles en ligne de commande.
- `exploration/` : scripts de contrôle et d'exploration des données.
- `donnees/` : tableau journalier.

## Auteur

[Prénom Nom], INF-5103, automne 2026.
