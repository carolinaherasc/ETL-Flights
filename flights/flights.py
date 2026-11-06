#https://openskynetwork.github.io/opensky-api/python.html

import time
import csv
import os
from opensky_api import OpenSkyApi, TokenManager

def extract_flight_data(airport_icao="EIDW", hours_back=23, output_csv="vuelos_dublin_raw.csv"):
    credentials_path = "credentials.json"

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(f"Missing '{credentials_path}'. Ensure it is located in the working directory.")

    print(f"Loading credentials from {credentials_path}...")
    token_mgr = TokenManager.from_json_file(credentials_path)
    api = OpenSkyApi(token_manager=token_mgr)

    # OpenSky: not exceed 1 UTC calendar day
    end_time = int(time.time())
    begin_time = end_time - (hours_back * 3600)

    arrivals = api.get_arrivals_by_airport(airport_icao, begin_time, end_time)
    departures = api.get_departures_by_airport(airport_icao, begin_time, end_time)

    total_arrivals = len(arrivals) if arrivals else 0
    total_departures = len(departures) if departures else 0
    print(f"Retrieved: {total_arrivals} arrivals and {total_departures} departures.")

    fieldnames = [
        "tipo_vuelo",
        "callsign",
        "icao24",
        "aeropuerto_origen",
        "aeropuerto_destino",
        "salida_unix",
        "llegada_unix"
    ]

    with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        if arrivals:
            for flight in arrivals:
                writer.writerow({
                    "tipo_vuelo": "Llegada",
                    "callsign": flight.callsign,
                    "icao24": flight.icao24,
                    "aeropuerto_origen": flight.estDepartureAirport,
                    "aeropuerto_destino": flight.estArrivalAirport,
                    "salida_unix": flight.firstSeen,
                    "llegada_unix": flight.lastSeen
                })

        if departures:
            for flight in departures:
                writer.writerow({
                    "tipo_vuelo": "Salida",
                    "callsign": flight.callsign,
                    "icao24": flight.icao24,
                    "aeropuerto_origen": flight.estDepartureAirport,
                    "aeropuerto_destino": flight.estArrivalAirport,
                    "salida_unix": flight.firstSeen,
                    "llegada_unix": flight.lastSeen
                })

    print(f"Data saved successfully to '{output_csv}'. Total rows written: {total_arrivals + total_departures}")
    return output_csv

if __name__ == "__main__":
    extract_flight_data()