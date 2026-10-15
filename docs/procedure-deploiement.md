# Procédure de déploiement et d'exploitation

Cette procédure décrit une installation sur un serveur disposant de Python et
PostgreSQL. Exécuter les commandes depuis la racine du dépôt. Les commandes
PowerShell sont indiquées pour Windows ; le script Python de sauvegarde
fonctionne également sous Linux et macOS.

## 1. Prérequis

- Python 3 et `pip`
- PostgreSQL et les outils client `psql`, `pg_dump` et `pg_restore`
- Un compte PostgreSQL autorisé à créer le schéma et à lire les données
- Les exports CSV VéloVille, placés dans `data/`

Sous Windows, vérifier que les outils PostgreSQL sont dans le `PATH` :

```powershell
Get-Command psql, pg_dump, pg_restore
```

## 2. Installer et configurer l'application

Créer un environnement virtuel, installer les dépendances et créer le fichier
de configuration local :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Renseigner dans `.env` la variable `DATABASE_URL` avec l'URL PostgreSQL
`postgresql+psycopg://...` et définir `JWT_SECRET` avec une clé privée
aléatoire. Ne pas commiter `.env` ni communiquer ces valeurs.

Créer une base PostgreSQL vide et un rôle applicatif selon les règles de
l'organisation. Depuis PowerShell, appliquer le schéma puis créer les comptes
de recette :

```powershell
psql -U <utilisateur_admin> -d <base> -f sql/schema.sql
psql -U <utilisateur_admin> -d <base> -f sql/comptes.sql
```

Les noms entre chevrons sont à remplacer. `psql` demande le mot de passe sans
l'inscrire dans la commande. La configuration de l'application doit ensuite
pointer vers la base et le rôle appropriés dans `.env`.

## 3. Importer les données

Le script charge `.env` automatiquement. Vérifier que les trois fichiers CSV
attendus sont présents dans `data/`, puis lancer l'import :

```powershell
python scripts/importer.py
```

Le rapport d'import est écrit dans `docs/rapport_import.csv`. Les rejets et
avertissements sont consignés dans `docs/rejets_et_avertissements.csv`.
L'import est rejouable ; examiner ces rapports après chaque exécution.

## 4. Démarrer l'API et l'interface

Lancer les deux processus dans des terminaux distincts :

```powershell
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

```powershell
streamlit run front/app.py --server.address 0.0.0.0 --server.port 8501
```

Vérifier la documentation de l'API à `http://<serveur>:8000/docs`, puis
ouvrir l'interface à `http://<serveur>:8501` et se connecter avec un compte
de recette. Adapter les adresses réseau et les règles de pare-feu à
l'environnement de déploiement.

## 5. Sauvegarder la base

Vérifier que `pg_dump` est accessible et que `.env` désigne la base à
sauvegarder. Depuis Windows, lancer :

```powershell
python scripts/sauvegarde.py
```

Sous Linux ou macOS, le script shell existant peut également être utilisé :

```bash
bash scripts/sauvegarde.sh
```

Une archive PostgreSQL au format custom est créée dans `sauvegardes/`, avec
un nom horodaté. Le mot de passe est transmis à `pg_dump` par l'environnement
du processus, pas par ses arguments. Stocker les archives dans un
emplacement protégé et ne pas les commiter : elles peuvent contenir des
données de trajets. Cette sauvegarde est manuelle ; planifier son exécution
et sa rétention relève de l'exploitation du serveur.

## 6. Restaurer une sauvegarde

La restauration s'effectue dans la base indiquée par `DATABASE_URL` dans
`.env`. Vérifier soigneusement cette destination et conserver une sauvegarde
de son état actuel avant de continuer. L'opération est destructive : elle
remplace les objets présents dans l'archive. Préférer une base cible vide.

La restauration nécessite le paramètre explicite `--confirmer` :

```powershell
python scripts/sauvegarde.py --restaurer .\sauvegardes\veloville_<horodatage>.dump --confirmer
```

Après restauration, vérifier les tables et les données avec les outils
PostgreSQL, puis tester l'API et l'interface avant de remettre le service à
disposition. Ne jamais tester cette commande contre une base de production
sans procédure de changement et validation préalable.

## 7. Tests

Depuis l'environnement virtuel :

```powershell
pytest --cov=api/services --cov-report=term-missing
```
