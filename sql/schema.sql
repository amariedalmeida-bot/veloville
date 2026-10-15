-- Schéma de la base veloville (PostgreSQL 14+).
-- À compléter en respectant le contrat du sujet (types, clés, contraintes).
-- Le script doit être rejouable : prévoir les DROP ... IF EXISTS ou
-- CREATE TABLE IF NOT EXISTS.


--Schéma de la base veloville (PostgreSQL 14+ / compatible SQLite).
-- Script rejouable.

-- ---------------------------------------------------------------
--  Table station
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS station (
    station_id VARCHAR(50) PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    commune VARCHAR(100) NOT NULL,
    capacite INT NOT NULL CHECK (capacite > 0),
    latitude FLOAT,
    longitude FLOAT,
    date_mise_en_service DATE
);

-- ---------------------------------------------------------------
--  Table trajet
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trajet (
    trajet_id VARCHAR(50) PRIMARY KEY,
    velo_id VARCHAR(50),
    depart_horodatage TIMESTAMP NOT NULL,
    station_depart VARCHAR(50) NOT NULL,
    station_arrivee VARCHAR(50),
    duree_secondes INT NOT NULL CHECK (duree_secondes > 0),
    type_usager VARCHAR(50),
    usager_ref VARCHAR(100),
    FOREIGN KEY (station_depart) REFERENCES station(station_id),
    FOREIGN KEY (station_arrivee) REFERENCES station(station_id)
);

-- ---------------------------------------------------------------
--  Table incident
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS incident (
    incident_id VARCHAR(50) PRIMARY KEY,
    date_signalement TIMESTAMP NOT NULL,
    cible VARCHAR(20) NOT NULL,
    velo_id VARCHAR(50),
    station_id VARCHAR(50),
    type_incident VARCHAR(100),
    statut VARCHAR(20) NOT NULL DEFAULT 'ouvert'
        CHECK (statut IN ('ouvert', 'en_cours', 'resolu')),
    date_resolution TIMESTAMP,
    technicien VARCHAR(100),
    CHECK (
        (statut = 'resolu' AND date_resolution IS NOT NULL AND date_resolution >= date_signalement)
        OR
        (statut <> 'resolu' AND date_resolution IS NULL)
    ),
    CHECK (
        (cible = 'velo' AND velo_id IS NOT NULL AND btrim(velo_id) <> '' AND station_id IS NULL)
        OR
        (cible = 'station' AND station_id IS NOT NULL AND btrim(station_id) <> '' AND velo_id IS NULL)
    ),
    FOREIGN KEY (station_id) REFERENCES station(station_id)
);

-- ---------------------------------------------------------------
-- Table utilisateur
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS utilisateur (
    id_utilisateur SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL
        CHECK (role IN ('exploitant', 'direction'))
);

-- ---------------------------------------------------------------
--  Index utiles aux filtres et aux indicateurs
-- ---------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_trajet_depart_date ON trajet(depart_horodatage);
CREATE INDEX IF NOT EXISTS idx_trajet_station_dep ON trajet(station_depart);
CREATE INDEX IF NOT EXISTS idx_trajet_station_arr ON trajet(station_arrivee);
CREATE INDEX IF NOT EXISTS idx_incident_statut ON incident(statut);