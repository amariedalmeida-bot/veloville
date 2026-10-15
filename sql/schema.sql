-- Schéma de la base veloville (PostgreSQL 14+).
-- À compléter en respectant le contrat du sujet (types, clés, contraintes).
-- Le script doit être rejouable : prévoir les DROP ... IF EXISTS ou
-- CREATE TABLE IF NOT EXISTS.


--Schéma de la base veloville (PostgreSQL 14+ / compatible SQLite).
-- Script rejouable.

-- ---------------------------------------------------------------
-- 1. Table station
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS station (
    station_id VARCHAR(50) PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    commune VARCHAR(100) NOT NULL,
    capacite INT NOT NULL DEFAULT 0,
    latitude FLOAT,
    longitude FLOAT,
    date_mise_en_service DATE
);

-- ---------------------------------------------------------------
-- 2. Table trajet
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trajet (
    trajet_id VARCHAR(50) PRIMARY KEY,
    velo_id VARCHAR(50),
    depart_horodatage TEXT NOT NULL,
    station_depart VARCHAR(50) NOT NULL,
    station_arrivee VARCHAR(50),
    duree_secondes INT NOT NULL DEFAULT 0,
    type_usager VARCHAR(50),
    usager_ref VARCHAR(100),
    FOREIGN KEY (station_depart) REFERENCES station(station_id),
    FOREIGN KEY (station_arrivee) REFERENCES station(station_id)
);

-- ---------------------------------------------------------------
-- 3. Table incident
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS incident (
    incident_id VARCHAR(50) PRIMARY KEY,
    date_signalement TEXT NOT NULL,
    cible VARCHAR(20) NOT NULL,
    velo_id VARCHAR(50),
    station_id VARCHAR(50),
    type_incident VARCHAR(100),
    statut VARCHAR(20) NOT NULL DEFAULT 'ouvert',
    date_resolution TEXT,
    technicien VARCHAR(100),
    FOREIGN KEY (station_id) REFERENCES station(station_id)
);

-- ---------------------------------------------------------------
-- 4. Table utilisateur
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS utilisateur (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user'
);

-- ---------------------------------------------------------------
-- 5. Index utiles aux filtres et aux indicateurs
-- ---------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_trajet_depart_date ON trajet(depart_horodatage);
CREATE INDEX IF NOT EXISTS idx_trajet_station_dep ON trajet(station_depart);
CREATE INDEX IF NOT EXISTS idx_trajet_station_arr ON trajet(station_arrivee);
CREATE INDEX IF NOT EXISTS idx_incident_statut ON incident(statut);