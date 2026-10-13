-- Schéma de la base veloville (PostgreSQL 14+).
-- À compléter en respectant le contrat du sujet (types, clés, contraintes).
-- Le script doit être rejouable : prévoir les DROP ... IF EXISTS ou
-- CREATE TABLE IF NOT EXISTS.

DROP TABLE IF EXISTS incident CASCADE;
DROP TABLE IF EXISTS trajet CASCADE;
DROP TABLE IF EXISTS utilisateur CASCADE;
DROP TABLE IF EXISTS station CASCADE;

-- ---------------------------------------------------------------
-- 1. Table station
-- ---------------------------------------------------------------
CREATE TABLE station (
    station_id VARCHAR(10) PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    commune VARCHAR(100) NOT NULL,
    capacite INTEGER NOT NULL CHECK (capacite > 0),
    latitude NUMERIC(8, 5) NOT NULL,
    longitude NUMERIC(8, 5) NOT NULL,
    date_mise_en_service DATE NOT NULL
);

-- ---------------------------------------------------------------
-- 2. Table trajet
-- ---------------------------------------------------------------
CREATE TABLE trajet (
    trajet_id VARCHAR(12) PRIMARY KEY,
    velo_id VARCHAR(8) NOT NULL,
    depart_horodatage TIMESTAMP NOT NULL,
    station_depart VARCHAR(10) NOT NULL REFERENCES station(station_id),
    station_arrivee VARCHAR(10) REFERENCES station(station_id),
    duree_secondes INTEGER NOT NULL CHECK (duree_secondes > 0),
    type_usager VARCHAR(50) NOT NULL,
    usager_ref VARCHAR(100)
);

-- ---------------------------------------------------------------
-- 3. Table incident
-- ---------------------------------------------------------------
CREATE TABLE incident (
    incident_id VARCHAR(12) PRIMARY KEY,
    date_signalement TIMESTAMP NOT NULL,
    cible VARCHAR(50) NOT NULL,
    velo_id VARCHAR(8),
    station_id VARCHAR(10) REFERENCES station(station_id),
    type_incident VARCHAR(50) NOT NULL,
    statut VARCHAR(20) NOT NULL CHECK (statut IN ('ouvert', 'en_cours', 'resolu')),
    date_resolution TIMESTAMP,
    technicien VARCHAR(100)
);

-- ---------------------------------------------------------------
-- 4. Table utilisateur
-- ---------------------------------------------------------------
CREATE TABLE utilisateur (
    id_utilisateur SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    mot_de_passe_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('exploitant', 'direction'))
);

-- ---------------------------------------------------------------
-- 5. Index utiles aux filtres et aux indicateurs
-- ---------------------------------------------------------------
-- Accélération des filtres par date et par station pour les trajets
CREATE INDEX idx_trajet_depart_horodatage ON trajet(depart_horodatage);
CREATE INDEX idx_trajet_station_depart ON trajet(station_depart);
CREATE INDEX idx_trajet_station_arrivee ON trajet(station_arrivee);

-- Accélération des filtres d'incidents (par statut et par date)
CREATE INDEX idx_incident_statut ON incident(statut);
CREATE INDEX idx_incident_date_signalement ON incident(date_signalement);

-- Accélération des filtres par commune
CREATE INDEX idx_station_commune ON station(commune);