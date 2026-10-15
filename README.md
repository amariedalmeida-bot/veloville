# VéloVille — Plateforme de valorisation des données

À compléter : présentation du projet, prérequis, installation, lancement de
l'API et du front, exécution des tests, liens vers la documentation
(docs/), auteur et version.


### Journal des rejets et avertissements
Le journal d'importation et de fiabilisation est disponible ici : `docs/rejets_et_avertissements.csv`.

## Couverture des tests

La couverture des modules métiers (`api/services/`) mesurée avec `pytest-cov` est de **85 %** (exigence minimale : 60 %).

Commande d'exécution :
```bash
pytest --cov=api/services --cov-report=term-missing