# VéloVille — Plateforme de valorisation des données

Application de consultation des stations, trajets, incidents et indicateurs
du service VéloVille. L'API FastAPI et l'interface Streamlit s'appuient sur
PostgreSQL ; l'accès aux routes métier est protégé par un jeton JWT.

Version initiale : `0.1.0` (voir le [journal des versions](CHANGELOG.md)).

## Prérequis

- Python et pip
- PostgreSQL, avec une base créée pour VéloVille
- `psql` pour appliquer les scripts SQL

## Installation et configuration

Depuis la racine du dépôt, créez un environnement virtuel et installez les
dépendances :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Renseignez `DATABASE_URL` et `JWT_SECRET` dans `.env`. La clé JWT est
obligatoire ; générez une valeur privée avec :

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Ne partagez pas cette valeur et ne commitez jamais `.env`. Configurez la base
de données, puis appliquez le schéma et les comptes :

```powershell
psql -U <utilisateur> -d <base> -f sql/schema.sql
psql -U <utilisateur> -d <base> -f sql/comptes.sql
```

Le script d'import charge automatiquement `DATABASE_URL` depuis `.env` :

```powershell
python scripts/importer.py
```

La [procédure de déploiement](docs/procedure-deploiement.md) décrit aussi la
sauvegarde et la restauration de la base.

## Lancement

Depuis la racine, démarrez l'API et l'interface dans deux terminaux distincts :

```powershell
uvicorn api.main:app --reload
```

```powershell
streamlit run front/app.py
```

L'interface est accessible à `http://localhost:8501` et la documentation
interactive de l'API à `http://127.0.0.1:8000/docs`.

## Tests

Lancer l'ensemble des tests et mesurer la couverture des services métier :

```powershell
pytest --cov=api/services --cov-report=term-missing
```

## Couverture des tests

Dernier relevé complet : **90 %** sur `api/services/`, avec 52 tests réussis
(exigence minimale : 60 %). Ce résultat inclut les tests unitaires et
d'intégration ; il peut évoluer avec les changements du projet.

## Documentation et journaux

- [Schéma de données](docs/schema-donnees.md)
- [Matrice des rôles et droits](docs/matrice-roles-droits.md)
- [Plan de recette](docs/recette/plan-de-recette.md) et
  [résultats de recette](docs/recette/resultats-recette.md)
- Journal des rejets et avertissements : `docs/rejets_et_avertissements.csv`
- Journal d'import : `docs/rapport_import.csv`