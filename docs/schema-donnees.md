# Schéma de données — VéloVille V1

Ce document présente la modélisation de la base de données relationnelle mise en place pour la plateforme VéloVille V1. Il s'appuie sur les besoins exprimés dans le cahier des charges et respecte les conventions de la méthode Merise.

---

## 1. Modèle Logique de Données (MLD textuel)

La base de données est structurée autour de 4 tables pour couvrir les données d'exploitation et la gestion des accès (clés primaires soulignées et clés étrangères signalées par un dièse `#`) :

- **STATION** (<u>station_id</u>, nom, commune, capacite, latitude, longitude, date_mise_en_service)
- **TRAJET** (<u>trajet_id</u>, velo_id, depart_horodatage, #station_depart, #station_arrivee, duree_secondes, type_usager, usager_ref)
- **INCIDENT** (<u>incident_id</u>, date_signalement, cible, velo_id, #station_id, type_incident, statut, date_resolution, technicien)
- **UTILISATEUR** (<u>id</u>, username, mot_de_passe_hash, role)

---

## 2. Description des tables et dictionnaire des données

### Table `STATION`
Cette table sert de référentiel pour l'ensemble des 120 stations du réseau.

| Attribut | Type SQL | Nullable | Contraintes / Clés | Description métier |
|---|---|---|---|---|
| `station_id` | `VARCHAR(10)` | Non | `PRIMARY KEY` | Identifiant unique de la station (ex. `S001`) |
| `nom` | `VARCHAR(150)` | Non | | Nom usuel combinant la ville et le lieu (ex. `Lille - Gare`) |
| `commune` | `VARCHAR(100)` | Non | | Commune de la métropole d'implantation |
| `capacite` | `INTEGER` | Non | `CHECK (capacite > 0)` | Nombre de bornes d'attache disponibles (RG1) |
| `latitude` | `NUMERIC(8, 5)` | Oui | | Coordonnée géographique WGS84 |
| `longitude` | `NUMERIC(8, 5)` | Oui | | Coordonnée géographique WGS84 |
| `date_mise_en_service` | `DATE` | Non | | Date d'ouverture de la station au public |

---

### Table `TRAJET`
Elle enregistre chaque location de vélo effectuée sur le réseau.

| Attribut | Type SQL | Nullable | Contraintes / Clés | Description métier |
|---|---|---|---|---|
| `trajet_id` | `VARCHAR(20)` | Non | `PRIMARY KEY` | Identifiant unique de la location (ex. `T480001`) |
| `velo_id` | `VARCHAR(10)` | Non | | Identifiant du vélo emprunté (ex. `V1167`) |
| `depart_horodatage` | `TIMESTAMP` | Non | | Date et heure de début du trajet |
| `station_depart` | `VARCHAR(10)` | Non | `FOREIGN KEY -> STATION(station_id)` | Station d'emprunt obligatoire (RG2) |
| `station_arrivee` | `VARCHAR(10)` | Oui | `FOREIGN KEY -> STATION(station_id)` | Station de retour (NULL si le vélo n'est pas encore rendu - RG3) |
| `duree_secondes` | `INTEGER` | Non | `CHECK (duree_secondes > 0)` | Temps de parcours réel en secondes (RG4) |
| `type_usager` | `VARCHAR(20)` | Non | `CHECK (type_usager IN ('abonne', 'occasionnel'))` | Profil d'utilisateur |
| `usager_ref` | `VARCHAR(50)` | Oui | | Pseudonyme haché de l'abonné (RG5) |

---

### Table `INCIDENT`
Elle centralise le suivi des dysfonctionnements signalés sur le terrain.

| Attribut | Type SQL | Nullable | Contraintes / Clés | Description métier |
|---|---|---|---|---|
| `incident_id` | `VARCHAR(20)` | Non | `PRIMARY KEY` | Identifiant du ticket de maintenance (ex. `I2026-0001`) |
| `date_signalement` | `TIMESTAMP` | Non | | Date et heure de création du ticket |
| `cible` | `VARCHAR(10)` | Non | `CHECK (cible IN ('velo', 'station'))` | Élément défaillant (RG6) |
| `velo_id` | `VARCHAR(10)` | Oui | | Renseigné uniquement si l'incident touche un vélo |
| `station_id` | `VARCHAR(10)` | Oui | `FOREIGN KEY -> STATION(station_id)` | Renseigné uniquement si l'incident touche une station |
| `type_incident` | `VARCHAR(100)` | Non | | Type de problème rencontré (ex. frein, pneu, borne) |
| `statut` | `VARCHAR(20)` | Non | `CHECK (statut IN ('ouvert', 'en_cours', 'resolu'))` | Étape de traitement du ticket (RG7) |
| `date_resolution` | `TIMESTAMP` | Oui | | Horodatage de fin d'intervention (RG8) |
| `technicien` | `VARCHAR(100)` | Oui | | Nom de l'agent intervenant sur la panne |

---

### Table `UTILISATEUR`
Elle gère les accès sécurisés à l'API et au tableau de bord.

| Attribut | Type SQL | Nullable | Contraintes / Clés | Description métier |
|---|---|---|---|---|
| `id` | `SERIAL` | Non | `PRIMARY KEY` | Identifiant technique auto-incrémenté |
| `username` | `VARCHAR(50)` | Non | `UNIQUE` | Identifiant de connexion unique |
| `mot_de_passe_hash` | `VARCHAR(255)` | Non | | Mot de passe sécurisé haché en bcrypt |
| `role` | `VARCHAR(20)` | Non | `CHECK (role IN ('exploitant', 'direction'))` | Droits applicatifs attribués |

---

## 3. Clés et relations entre les données

1. **Clés primaires (PK)** :  
   Chaque table dispose d'un identifiant unique : `station_id`, `trajet_id` et `incident_id` s'appuient sur les identifiants métier fournis par les exports, tandis qu'`utilisateur` utilise un identifiant technique `id` associé à un `username` unique.

2. **Clés étrangères (FK)** :  
   - `TRAJET.station_depart` pointe vers `STATION.station_id` : il sera donc impossible d'enregistrer un trajet sans point de départ.
   - `TRAJET.station_arrivee` pointe aussi vers `STATION.station_id`, mais autorise la valeur vide (NULL) pour gérer le cas réel des vélos non encore restitués au moment de l'export.
   - `INCIDENT.station_id` pointe vers `STATION.station_id` : permet de relier un incident technique à sa station d'origine lorsqu'elle est concernée.

---

## 4. Règles de gestion portées par le schéma relationnel

- **RG1 (Capacité strictement positive)** : une contrainte `CHECK (capacite > 0)` interdit les stations à 0 place.
- **RG2 & RG3 (Validité des stations)** : l'intégrité référentielle empêche de lier un trajet à une station fictive.
- **RG4 (Durée positive)** : la contrainte `CHECK (duree_secondes > 0)` écarte les trajets aberrants de 0 seconde ou négatifs.
- **RG5 (Protection des données / RGPD)** : la base ne conserve que le pseudonyme technique `usager_ref` et ne stocke aucune donnée nominative.
- **RG6 (Exclusivité de la cible)** : une contrainte `CHECK` vérifie qu'un incident vise soit un vélo, soit une station, mais jamais les deux en même temps ni aucun des deux.
- **RG7 (Machine à états des statuts)** : le champ `statut` est borné par `CHECK` aux seules valeurs `ouvert`, `en_cours` et `resolu`.
- **RG8 (Cohérence des dates de résolution)** : une contrainte `CHECK` s'assure qu'une date de résolution n'existe que si le statut est `resolu`, et qu'elle est toujours postérieure ou égale à la date du signalement.
