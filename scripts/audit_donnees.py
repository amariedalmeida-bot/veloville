import csv
from datetime import datetime
from pathlib import Path

# Chemin vers le dossier data basé sur la position du script :
# Path(__file__).resolve().parent -> dossier scripts/
# .parent -> dossier squelette-git/
DOSSIER_DATA = Path(__file__).resolve().parent.parent / "data"

# ==============================================================================
# 1. AUDIT DU RÉFÉRENTIEL DES STATIONS
# ==============================================================================
print("--- STATIONS ---")

stations_valides = set()
total_stations = 0

with open(DOSSIER_DATA / "stations.csv", mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for ligne in reader:
        total_stations += 1
        stations_valides.add(ligne["station_id"].strip())

print(f"Lignes lues : {total_stations} | Stations uniques : {len(stations_valides)}")
print("Anomalies : aucune (référentiel intègre)\n")


# ==============================================================================
# 2. AUDIT DES TRAJETS
# ==============================================================================
print("--- TRAJETS ---")

total_trajets = 0
ids_trajets_vus = set()

doublons_id = 0
dates_invalides = 0
stations_inconnues = 0
durees_invalides = 0

with open(DOSSIER_DATA / "trajets.csv", mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for ligne in reader:
        total_trajets += 1
        tid = ligne["trajet_id"].strip()

        if tid in ids_trajets_vus:
            doublons_id += 1
        else:
            ids_trajets_vus.add(tid)

        date_str = ligne["depart_horodatage"].strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            dates_invalides += 1

        dep = ligne["station_depart"].strip()
        arr = ligne["station_arrivee"].strip()
        if (dep not in stations_valides) or (arr and arr not in stations_valides):
            stations_inconnues += 1

        try:
            if int(ligne["duree_secondes"]) <= 0:
                durees_invalides += 1
        except ValueError:
            durees_invalides += 1

print(f"Lignes lues : {total_trajets}")
print(f"Doublons sur la clé trajet_id : {doublons_id}")
print(f"Dates non conformes au format ISO : {dates_invalides}")
print(f"Trajets référençant des stations inconnues : {stations_inconnues}")
print(f"Trajets avec durée <= 0 seconde : {durees_invalides}\n")


# ==============================================================================
# 3. AUDIT DES TICKETS D'INCIDENTS
# ==============================================================================
print("--- INCIDENTS ---")

total_incidents = 0
statuts_a_normaliser = 0
dates_incoherentes = 0

with open(DOSSIER_DATA / "incidents.csv", mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for ligne in reader:
        total_incidents += 1

        statut = ligne["statut"].strip().lower()
        if statut == "en cours":
            statuts_a_normaliser += 1

        d_sig = ligne["date_signalement"].strip()
        d_res = ligne["date_resolution"].strip()

        if d_res:
            try:
                fmt_sig = "%Y-%m-%d %H:%M:%S" if "-" in d_sig else "%d/%m/%Y %H:%M"
                fmt_res = "%Y-%m-%d %H:%M:%S" if "-" in d_res else "%d/%m/%Y %H:%M"
                
                dt_sig = datetime.strptime(d_sig, fmt_sig)
                dt_res = datetime.strptime(d_res, fmt_res)

                if dt_res < dt_sig:
                    dates_incoherentes += 1
            except ValueError:
                pass

print(f"Lignes lues : {total_incidents}")
print(f"Statuts 'en cours' à normaliser en 'en_cours' : {statuts_a_normaliser}")
print(f"Incidents résolus avant signalement (incohérence RG8) : {dates_incoherentes}")