# https://openskynetwork.github.io/opensky-api/python.html

import time
import csv
import os
from opensky_api import OpenSkyApi, TokenManager
import pandas as pd
import os

def extractFlightData(airportIcao="EIDW", hoursBack=23, outputCsv="dublinFlightsRaw.csv"):
    credentialsPath = "credentials.json"

    if not os.path.exists(credentialsPath):
        raise FileNotFoundError(f"Missing '{credentialsPath}'. Ensure it is located in the working directory.")

    print(f"Loading credentials from {credentialsPath}...")
    tokenMgr = TokenManager.from_json_file(credentialsPath)
    api = OpenSkyApi(token_manager=tokenMgr)

    # OpenSky: not exceed 1 UTC calendar day
    endTime = int(time.time())
    beginTime = endTime - (hoursBack * 3600)

    arrivals = api.get_arrivals_by_airport(airportIcao, beginTime, endTime)
    departures = api.get_departures_by_airport(airportIcao, beginTime, endTime)

    totalArrivals = len(arrivals) if arrivals else 0
    totalDepartures = len(departures) if departures else 0
    print(f"Retrieved: {totalArrivals} arrivals and {totalDepartures} departures.")

    fieldNames = [
        "flightType",
        "callsign",
        "icao24",
        "originAirport",
        "destinationAirport",
        "departureUnix",
        "arrivalUnix",
        "originHorizDistance",
        "originVertDistance",
        "destinationHorizDistance",
        "destinationVertDistance"
    ]

    with open(outputCsv, mode="w", newline="", encoding="utf-8") as csvFile:
        writer = csv.DictWriter(csvFile, fieldnames=fieldNames)
        writer.writeheader()

        if arrivals:
            for flight in arrivals:
                writer.writerow({
                    "flightType": "Arrival",
                    "callsign": flight.callsign,
                    "icao24": flight.icao24,
                    "originAirport": flight.estDepartureAirport,
                    "destinationAirport": flight.estArrivalAirport,
                    "departureUnix": flight.firstSeen,
                    "arrivalUnix": flight.lastSeen,
                    "originHorizDistance": flight.estDepartureAirportHorizDistance,
                    "originVertDistance": flight.estDepartureAirportVertDistance,
                    "destinationHorizDistance": flight.estArrivalAirportHorizDistance,
                    "destinationVertDistance": flight.estArrivalAirportVertDistance
                })

        if departures:
            for flight in departures:
                writer.writerow({
                    "flightType": "Departure",
                    "callsign": flight.callsign,
                    "icao24": flight.icao24,
                    "originAirport": flight.estDepartureAirport,
                    "destinationAirport": flight.estArrivalAirport,
                    "departureUnix": flight.firstSeen,
                    "arrivalUnix": flight.lastSeen,
                    "originHorizDistance": flight.estDepartureAirportHorizDistance,
                    "originVertDistance": flight.estDepartureAirportVertDistance,
                    "destinationHorizDistance": flight.estArrivalAirportHorizDistance,
                    "destinationVertDistance": flight.estArrivalAirportVertDistance
                })

    print(f"Data saved successfully to '{outputCsv}'. Total rows written: {totalArrivals + totalDepartures}")
    return outputCsv


def loadData(filePath):
    if not os.path.exists(filePath):
        print(f"Error: File '{filePath}' not found.")
        return None
    df = pd.read_csv(filePath)
    return df

def cleanData(df):
    #Remove duplicates
    df = df.drop_duplicates()

    #Standardize and clean Callsign
    df["callsign"] = df["callsign"].astype(str).str.strip()
    df["callsign"] = df["callsign"].replace([""], "UNKNOWN")

    # Fill missing airport information
    df["originAirport"] = df["originAirport"].fillna("UNKNOWN")
    df["destinationAirport"] = df["destinationAirport"].fillna("UNKNOWN")

    #Replace missing distance
    distanceCols = ["originHorizDistance","originVertDistance","destinationHorizDistance","destinationVertDistance"]

    for col in distanceCols:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)

    #Filter out invalid flight records
    validFlights = df["arrivalUnix"] > df["departureUnix"]
    df = df[validFlights]

    return df


if __name__ == "__main__":
    #extractFlightData()
    
    rawFile = "dublinFlightsRaw.csv"
    rawDf = loadData(rawFile)
    print("Load")
    
    cleanDf = cleanData(rawDf)
    print("Clean")