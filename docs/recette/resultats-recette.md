# Résultats du plan de recette — VéloVille V1

**Date de recette :** 2026-09-01  
**Environnement :** Python 3.14 / PostgreSQL \& SQLite / Streamlit  
**Testeur :** Administrateur / Candidat E2

\---

## Synthèse de la recette

|Total des cas|Conformes (OK)|Non conformes (KO)|Non testés (NT)|Taux de conformité|
|:-:|:-:|:-:|:-:|:-:|
|**10**|**10**|**0**|**0**|**100 %**|

\---

## Détail des résultats d'exécution

### REC-01 — Import idempotent

* **Objectif :** Vérifier qu'une seconde exécution de l'import ne modifie pas la base.
* **Résultat attendu :** Les deux exécutions se terminent sans erreur ; comptages identiques (Stations = 120, Trajets = 2002, Incidents = 177).
* **Résultat obtenu :** Exécution sans erreur. Les comptages post-import sont strictement identiques : Stations = 120, Trajets = 2002, Incidents = 177.
* **Statut :** **OK**

### REC-02 — Rejets journalisés et cohérence des volumes

* **Objectif :** Vérifier que chaque ligne écartée est tracée avec son motif et que rien n'est perdu silencieusement.
* **Résultat attendu :** Pour chaque fichier : importées + rejetées + doublons = total lignes CSV. Requête `LEFT JOIN station\_arrivee` renvoie 0 orphelin.
* **Résultat obtenu :** La somme correspond exactement aux volumes sources des fichiers CSV. Le journal contient les 6 champs obligatoires (fichier source, identifiant, colonne, valeur, motif, décision). L'intégrité référentielle est totale (0 trajet orphelin).
* **Statut :** **OK**

### REC-03 — Connexion acceptée

* **Objectif :** Vérifier l'authentification avec un compte valide.
* **Résultat attendu :** `POST /auth/login` renvoie un code HTTP 200 avec un token JWT valide et le rôle associé.
* **Résultat obtenu :** Connexion réussie pour `exploitant01` et `direction01`. Code HTTP 200, jeton JWT `access\_token` émis avec type `bearer`.
* **Statut :** **OK**

### REC-04 — Connexion refusée

* **Objectif :** Vérifier le rejet d'identifiants erronés.
* **Résultat attendu :** Code HTTP 401 Unauthorized avec message d'erreur générique.
* **Résultat obtenu :** Authentification rejetée avec le code HTTP 401 et message explicite sans divulgation d'information sensible.
* **Statut :** **OK**

### REC-05 — Route protégée sans jeton

* **Objectif :** Vérifier le blocage d'accès aux ressources sans authentification.
* **Résultat attendu :** `GET /stations` sans header Authorization renvoie un code HTTP 401.
* **Résultat obtenu :** Requête rejetée avec le code HTTP 401 Unauthorized (`Not authenticated`).
* **Statut :** **OK**

### REC-06 — Rôle direction refusé sur la modification d'un incident

* **Objectif :** Vérifier le contrôle d'accès basé sur les rôles (RBAC).
* **Résultat attendu :** `PUT /incidents/{id}/statut` avec un jeton direction renvoie un code HTTP 403 Forbidden.
* **Résultat obtenu :** Code HTTP 403 Forbidden retourné. Seul le rôle exploitant est autorisé à modifier le statut d'un incident.
* **Statut :** **OK**

### REC-07 — Pagination

* **Objectif :** Vérifier la pagination et la validation des bornes.
* **Résultat attendu :** Structure paginée (`total`, `page`, `taille_page`, `resultats`). Paramètres hors bornes renvoient une erreur HTTP 422.
* **Résultat obtenu :** L'enveloppe JSON paginée retourne exactement le format attendu. Les requêtes avec `taille_page < 1` ou `taille_page > 100` lèvent bien une erreur HTTP 422 Unprocessable Entity.
* **Statut :** **OK**

### REC-08 — Station introuvable

* **Objectif :** Vérifier le comportement en cas de ressource inexistante.
* **Résultat attendu :** `GET /stations/99999` renvoie une erreur HTTP 404 Not Found.
* **Résultat obtenu :** Code HTTP 404 retourné avec le message textuel : `Station non trouvée`.
* **Statut :** **OK**

### REC-09 — Cohérence de l'indicateur « activité par jour » avec la base

* **Objectif :** Vérifier la conformité des données retournées par l'indicateur d'activité journalière avec les agrégats SQL.
* **Résultat attendu :** Les volumes quotidiens et durées moyennes correspondent aux requêtes SQL directes.
* **Résultat obtenu :** Concordance stricte entre la sortie JSON de l'API et les requêtes SQL directes sur la table `trajet`.
* **Statut :** **OK**

### REC-10 — Front : état vide et état d'erreur

* **Objectif :** Vérifier le respect des exigences UX et d'accessibilité sur Streamlit en cas d'erreur ou d'absence de données.
* **Résultat attendu :** Affichage d'un message textuel explicite en français sans trace technique Python brute (stacktrace) lorsque l'API est indisponible ou qu'aucun résultat ne correspond aux filtres.
* **Résultat obtenu :** Les trois états (chargement, vide, erreur) sont gérés. Lorsque l'API est coupée, l'interface affiche un bandeau rouge accessible invitant à vérifier le service, sans aucune exception Python non interceptée.
* **Statut :** **OK**
