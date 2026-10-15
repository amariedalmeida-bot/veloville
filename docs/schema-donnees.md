# Schéma de données

Description des quatre tables déclarées dans [`sql/schema.sql`](../sql/schema.sql).
Les types, nullabilités, clés et contraintes ci-dessous reflètent ce DDL.

---

## 1. Modèle Logique de Données (MLD textuel)

Les clés primaires sont soulignées ; les clés étrangères sont signalées par `#`.

- **STATION** (<u>station_id</u>, nom, commune, capacite, latitude, longitude, date_mise_en_service)
- **TRAJET** (<u>trajet_id</u>, velo_id, depart_horodatage, #station_depart, #station_arrivee, duree_secondes, type_usager, usager_ref)
- **INCIDENT** (<u>incident_id</u>, date_signalement, cible, velo_id, #station_id, type_incident, statut, date_resolution, technicien)
- **UTILISATEUR** (<u>id_utilisateur</u>, username, mot_de_passe_hash, role)

---

## 2. Description des tables et dictionnaire des données

### Table `STATION`

Référentiel des stations du réseau.

| Attribut | Type SQL | Nullable | Contraintes / Clés | Description métier |
|---|---|---|---|---|
| `station_id` | `VARCHAR(50)` | Non | `PRIMARY KEY` | Identifiant unique de la station (ex. `S001`) |
| `nom` | `VARCHAR(255)` | Non | | Nom usuel de la station |
| `commune` | `VARCHAR(100)` | Non | | Commune d'implantation |
| `capacite` | `INT` | Non | `CHECK (capacite > 0)` | Capacité de la station (RG1) |
| `latitude` | `FLOAT` | Oui | | Coordonnée géographique |
| `longitude` | `FLOAT` | Oui | | Coordonnée géographique |
| `date_mise_en_service` | `DATE` | Oui | | Date d'ouverture de la station au public |

### Table `TRAJET`

Enregistre les locations de vélos.

| Attribut | Type SQL | Nullable | Contraintes / Clés | Description métier |
|---|---|---|---|---|
| `trajet_id` | `VARCHAR(50)` | Non | `PRIMARY KEY` | Identifiant unique du trajet |
| `velo_id` | `VARCHAR(50)` | Oui | | Identifiant du vélo |
| `depart_horodatage` | `TIMESTAMP` | Non | | Date et heure de départ |
| `station_depart` | `VARCHAR(50)` | Non | `FOREIGN KEY -> STATION(station_id)` | Station de départ obligatoire (RG2) |
| `station_arrivee` | `VARCHAR(50)` | Oui | `FOREIGN KEY -> STATION(station_id)` | Station d'arrivée, éventuellement inconnue (RG3) |
| `duree_secondes` | `INT` | Non | `CHECK (duree_secondes > 0)` | Durée du trajet en secondes (RG4) |
| `type_usager` | `VARCHAR(50)` | Oui | | Type d'usager |
| `usager_ref` | `VARCHAR(100)` | Oui | | Pseudonyme d'usager, le cas échéant (RG5) |

### Table `INCIDENT`

Enregistre les signalements de maintenance.

| Attribut | Type SQL | Nullable | Contraintes / Clés | Description métier |
|---|---|---|---|---|
| `incident_id` | `VARCHAR(50)` | Non | `PRIMARY KEY` | Identifiant unique de l'incident |
| `date_signalement` | `TIMESTAMP` | Non | | Date et heure du signalement |
| `cible` | `VARCHAR(20)` | Non | `CHECK` d'exclusivité décrit en RG6 | Type de cible : vélo ou station (RG6) |
| `velo_id` | `VARCHAR(50)` | Oui | | Référence du vélo si la cible est un vélo |
| `station_id` | `VARCHAR(50)` | Oui | `FOREIGN KEY -> STATION(station_id)` | Référence de station si la cible est une station |
| `type_incident` | `VARCHAR(100)` | Oui | | Type de problème signalé |
| `statut` | `VARCHAR(20)` | Non | `DEFAULT 'ouvert'`, valeurs limitées par `CHECK` (RG7) | État de traitement |
| `date_resolution` | `TIMESTAMP` | Oui | Cohérence avec le statut et `date_signalement` (RG8) | Date et heure de résolution |
| `technicien` | `VARCHAR(100)` | Oui | | Nom du technicien, le cas échéant |

### Table `UTILISATEUR`

Comptes utilisés pour l'authentification à l'API et au tableau de bord.

| Attribut | Type SQL | Nullable | Contraintes / Clés | Description métier |
|---|---|---|---|---|
| `id_utilisateur` | `SERIAL` | Non | `PRIMARY KEY` | Identifiant technique auto-incrémenté |
| `username` | `VARCHAR(100)` | Non | `UNIQUE` | Identifiant de connexion |
| `mot_de_passe_hash` | `VARCHAR(255)` | Non | | Empreinte du mot de passe |
| `role` | `VARCHAR(20)` | Non | `CHECK (role IN ('exploitant', 'direction'))` | Rôle applicatif |

---

## 3. Clés et relations entre les données

1. **Clés primaires (PK)** : `station_id`, `trajet_id` et `incident_id` identifient respectivement les stations, trajets et incidents. La table `utilisateur` utilise `id_utilisateur` comme clé technique et `username` est également unique.
2. **Clés étrangères (FK)** :
   - `TRAJET.station_depart` référence `STATION.station_id` et est obligatoire.
   - `TRAJET.station_arrivee` référence `STATION.station_id` et peut être `NULL`.
   - `INCIDENT.station_id` référence `STATION.station_id` et peut être `NULL` lorsque la cible est un vélo.

---

## 4. Règles de gestion portées par le schéma relationnel

- **RG1 — Capacité positive** : `CHECK (capacite > 0)`.
- **RG2/RG3 — Références des trajets** : la station de départ est obligatoire et les références de départ et d'arrivée sont protégées par des clés étrangères ; la station d'arrivée peut être `NULL`.
- **RG4 — Durée positive** : `CHECK (duree_secondes > 0)`.
- **RG5 — Pseudonymisation** : le schéma comporte `usager_ref`, sans table d'abonnés ni donnée directement identifiante. La relation entre le type d'usager et la présence du pseudonyme n'est pas contrainte par ce DDL.
- **RG6 — Cible d'incident exclusive** : une contrainte `CHECK` impose `cible = 'velo'` avec `velo_id` renseigné et `station_id` nul, ou `cible = 'station'` avec `station_id` renseigné et `velo_id` nul. Les références non vides sont également exigées.
- **RG7 — Statuts d'incident** : `statut` est limité à `ouvert`, `en_cours` et `resolu`. Les transitions autorisées sont contrôlées par le service applicatif.
- **RG8 — Dates de résolution** : la contrainte impose une date de résolution non nulle et postérieure ou égale au signalement pour un incident `resolu`, et une date nulle pour les autres statuts.
- **Rôles** : le rôle utilisateur est limité à `exploitant` ou `direction`.

Le schéma crée également des index sur `trajet.depart_horodatage`,
`trajet.station_depart`, `trajet.station_arrivee` et `incident.statut`.

---

## 5. Rapport d'audit des exports bruts de billettique
Les trois fichiers sources ont été recompilés à partir des données brutes avec
les fonctions de validation de `api/services/fiabilisation.py`. Les volumes
bruts sont de 120 stations, 2 030 trajets et 180 incidents.

### Synthèse des anomalies dans les fichiers sources

| Fichier source | Volume brut | Règle / critère | Anomalie constatée | Nombre de lignes sources | Traitement prévu |
|---|---:|---|---|---:|---|
| `stations.csv` | 120 | Référentiel | Aucune anomalie détectée | 0 | Importation intégrale |
| `trajets.csv` | 2 030 | Doublons stricts | Ligne strictement identique à une ligne précédente | 12 | Écarter la répétition |
| `trajets.csv` | 2 030 | Format d'horodatage | Horodatage nécessitant une normalisation | 5 | Conversion au format ISO |
| `trajets.csv` | 2 030 | RG2/RG3 | Référence de station inconnue à l'arrivée | 7 | Rejet journalisé |
| `trajets.csv` | 2 030 | RG4 | Durée nulle ou négative | 10 | Rejet journalisé |
| `incidents.csv` | 180 | RG7 | Statut nécessitant une normalisation (casse ou espaces) | 125 | Normalisation vers un statut valide |
| `incidents.csv` | 180 | RG7 | Dont statut `en cours` avec espace | 46 | Normalisation vers `en_cours` |
| `incidents.csv` | 180 | RG8 | Date de résolution antérieure au signalement | 3 | Rejet journalisé |

Les critères comptent les anomalies brutes par règle et peuvent se chevaucher ;
leur somme n'est donc pas le nombre de lignes uniques à rejeter. L'importeur
traite les doublons avant les validations suivantes et journalise le premier
motif de rejet rencontré. Cela explique notamment que son journal contienne
9 rejets pour durée invalide alors que 10 lignes sources ont une durée
invalide, et 4 normalisations d'horodatage alors que 5 lignes en nécessitent
une.

Le journal `docs/rapport_import.csv` contient 419 événements pour ce jeu de
données : 28 rejets et 4 normalisations pour les trajets, puis 3 rejets et
384 normalisations pour les incidents. Il compte les événements de traitement
(normalisations comprises), et non les anomalies brutes par règle.