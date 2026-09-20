import json
from pathlib import Path
import pandas as pd
from sqlalchemy import Float, String, create_engine


def process_raw_data():
    readings_file = Path("data/raw/raw_readings.json")
    stations_file = Path("data/raw/raw_stations.json")

    if not readings_file.exists():
        print("Error: data/raw/raw_readings.json not found.")
        return

    # 1. Parse Station Metadata (Latitude & Longitude)
    station_coords = {}
    if stations_file.exists():
        with open(stations_file, "r", encoding="utf-8") as f:
            st_payload = json.load(f)
            st_items = st_payload.get("items", [])
            for st_item in st_items:
                ref = st_item.get(
                    "stationReference", st_item.get("notation")
                )
                lat = st_item.get("lat")
                lon = st_item.get("long")
                town = st_item.get("town", st_item.get("label", "Unknown"))
                if ref and lat is not None and lon is not None:
                    station_coords[str(ref)] = {
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "town": str(town),
                    }

    # 2. Parse Telemetry Readings
    records = []
    with open(readings_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    items = (
        payload.get("items", []) if isinstance(payload, dict) else payload
    )

    for item in items:
        if not isinstance(item, dict):
            continue

        val = None
        date_time = None
        latest_reading = item.get("latestReading")

        if isinstance(latest_reading, dict):
            val = latest_reading.get("value")
            date_time = latest_reading.get("dateTime")
        elif "value" in item:
            val = item.get("value")

        station_ref = str(
            item.get(
                "stationReference",
                item.get("notation", item.get("label", "Unknown")),
            )
        )

        if val is not None:
            # Match coordinates from station metadata map
            coords = station_coords.get(
                station_ref,
                {"latitude": None, "longitude": None, "town": "Unknown"},
            )

            records.append(
                {
                    "station_id": station_ref,
                    "town": coords["town"],
                    "parameter": str(
                        item.get(
                            "parameterName",
                            item.get("parameter", "Rainfall"),
                        )
                    ),
                    "unit_name": str(item.get("unitName", "mm")),
                    "qualifier": str(item.get("qualifier", "Analysis")),
                    "value": float(val),
                    "datetime": str(date_time) if date_time else None,
                    "latitude": coords["latitude"],
                    "longitude": coords["longitude"],
                }
            )

    df = pd.DataFrame(records)
    print(f"Extracted {len(df)} valid numerical records.")

    if df.empty:
        print("WARNING: No numerical values found.")
        return

    # Save processed data to SQLite
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{output_dir / 'rainfall.db'}")

    df.to_sql(
        "rainfall_measures",
        con=engine,
        if_exists="replace",
        index=False,
        dtype={
            "value": Float(),
            "station_id": String(50),
            "town": String(100),
            "datetime": String(50),
            "latitude": Float(),
            "longitude": Float(),
        },
    )
    print("Database updated with numerical values and station coordinates!")


if __name__ == "__main__":
    process_raw_data()



