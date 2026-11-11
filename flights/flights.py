# https://openskynetwork.github.io/opensky-api/python.html

import time
import csv
import os
from opensky_api import OpenSkyApi, TokenManager
import pandas as pd
import numpy as np
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

def transformData(df):
    #Dates and Times
    df["departureTime"] = pd.to_datetime(df["departureUnix"], unit='s')
    df["arrivalTime"] = pd.to_datetime(df["arrivalUnix"], unit='s')
    df["arrivalHour"] = df["arrivalTime"].dt.hour
    df["departureHour"] = df["departureTime"].dt.hour
    df["dayOfWeek"] = df["arrivalTime"].dt.day_name()
    df["month"] = df["arrivalTime"].dt.month_name()

    #Identifying weekend flights (Saturday = 5, Sunday = 6)
    df["isWeekend"] = np.where(df["arrivalTime"].dt.day_of_week >= 5, "Weekend", "Weekday")

    #Flight duration and convert horizontal distances to kilometers
    df["durationMinutes"] = (df["arrivalUnix"] - df["departureUnix"]) / 60
    df["durationMinutes"] = df["durationMinutes"].round(2)

    df["originDistanceKm"] = (df["originHorizDistance"] / 1000).round(2)
    df["destDistanceKm"] = (df["destinationHorizDistance"] / 1000).round(2)

    #Categorization of flights based on duration
    df["flightCategory"] = np.where(df["durationMinutes"] < 180, "Short-Range",
                                    np.where(df["durationMinutes"] < 360, "Medium-Range", "Long-Range"))

    #Set time of day based on departure hour
    df["timeOfDay"] = np.where((df["departureHour"] >= 5) & (df["departureHour"] < 12), "Morning",
                               np.where((df["departureHour"] >= 12) & (df["departureHour"] < 17), "Afternoon",
                                        np.where((df["departureHour"] >= 17) & (df["departureHour"] < 22), "Evening", "Night")))

    #If both airports start with EI (Ireland) it is domestic
    df["flightScope"] = np.where((df["originAirport"].str.startswith("EI", na=False)) &
                                 (df["destinationAirport"].str.startswith("EI", na=False)),"Domestic", "International")

    #Get airline code from the first 3 letters of the callsign
    df["airlineCode"] = df["callsign"].str[:3]

    #Map codes to the actual airline names
    dublinAirlines = {
        "RYR": "Ryanair",
        "EIN": "Aer Lingus",
        "REA": "Emerald Airlines",
        "EZY": "easyJet",
        "BAW": "British Airways",
        "AFR": "Air France",
        "AAL": "American Airlines",
        "BCS": "European Air Transport / DHL",
        "CFE": "BA CityFlyer",
        "CHH": "Hainan Airlines",
        "DAL": "Delta Air Lines",
        "DLH": "Lufthansa",
        "EAI": "Emerald Airlines",
        "ETD": "Etihad Airways",
        "FDX": "FedEx Express",
        "FPO": "ASL Airlines France",
        "IBS": "Iberia Express",
        "KLM": "KLM Royal Dutch Airlines",
        "LGL": "Luxair",
        "LHX": "Lufthansa Cargo",
        "MSR": "EgyptAir",
        "NJE": "NetJets Europe",
        "QTR": "Qatar Airways",
        "SAS": "Scandinavian Airlines",
        "SWR": "Swiss International Air Lines",
        "THY": "Turkish Airlines",
        "TVF": "Transavia France",
        "UAE": "Emirates",
        "UAL": "United Airlines",
        "UPS": "UPS Airlines"
    }
    df["airlineName"] = df["airlineCode"].map(dublinAirlines).fillna("Other/Unknown")

    finalCols = [
        "flightType", "callsign", "airlineName", "icao24",
        "originAirport", "destinationAirport", "flightScope",
        "departureTime", "arrivalTime", "timeOfDay", "dayOfWeek", "isWeekend",
        "durationMinutes", "flightCategory",
        "originDistanceKm", "destDistanceKm"
    ]

    return df[finalCols]


if __name__ == "__main__":
    #extractFlightData()
    rawFile = "dublinFlightsRaw.csv"
    rawDf = loadData(rawFile)
    print("Load")

    cleanDf = cleanData(rawDf)
    print("Clean")

    transformDf=transformData(cleanDf)
    print("Transform")

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(transformDf.head())