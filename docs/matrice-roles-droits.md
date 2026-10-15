# Matrice rôles x droits

Cette matrice décrit les routes exposées par l'API V1. Les rôles
`exploitant` et `direction` doivent présenter un jeton valide. La connexion
est publique ; toute autre route métier est protégée.

| Méthode et route | Anonyme | Exploitant | Direction | Refus et cas particuliers |
|---|---|---|---|---|
| `GET /sante` | `200` | `200` | `200` | Route publique de vérification de disponibilité. |
| `POST /auth/login` | `200` si identifiants valides ; `401` sinon | Identique à anonyme | Identique à anonyme | `422` si le corps ne respecte pas le schéma de connexion. |
| `GET /stations/communes` | `401` | `200` | `200` | Route protégée, sans droit de modification. |
| `GET /stations` | `401` | `200` | `200` | Filtre par commune et pagination ; `422` si les paramètres de pagination sont hors limites. |
| `GET /stations/{station_id}` | `401` | `200` | `200` | `404` si la station n'existe pas. |
| `GET /trajets` | `401` | `200` | `200` | Filtres par période et station ; `422` si une date ou un paramètre de pagination est invalide. |
| `GET /incidents` | `401` | `200` | `200` | Filtre par statut et pagination ; `422` si les paramètres de pagination sont hors limites. |
| `PUT /incidents/{incident_id}/statut` | `401` | `200` si transition autorisée | `403` | `404` si l'incident n'existe pas ; `409` si la transition viole RG7 ou si la date de signalement est future ; `422` si le corps est invalide. |
| `GET /indicateurs/activite-par-jour` | `401` | `200` | `200` | `422` si une date de filtre est invalide. |
| `GET /indicateurs/stations-actives` | `401` | `200` | `200` | `422` si `limite` est hors limites. |
| `GET /indicateurs/incidents-par-statut` | `401` | `200` | `200` | Route protégée, en lecture seule. |

Les refus d'authentification renvoient `401 Unauthorized`. La modification
d'un incident est réservée à l'exploitant : la direction reçoit
`403 Forbidden`. Aucun rôle administrateur applicatif n'est prévu en V1.
