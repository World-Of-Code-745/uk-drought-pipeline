import json
from pathlib import Path
import urllib.request


def fetch_rainfall_data():
    # Endpoints for live readings and station locations
    readings_url = "https://environment.data.gov.uk/flood-monitoring/id/measures?parameter=rainfall"
    stations_url = "https://environment.data.gov.uk/flood-monitoring/id/stations?parameter=rainfall"

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching raw rainfall readings...")
    req = urllib.request.Request(
        readings_url, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as response:
        readings_data = json.loads(response.read().decode("utf-8"))

    readings_file = output_dir / "raw_readings.json"
    with open(readings_file, "w", encoding="utf-8") as f:
        json.dump(readings_data, f, indent=2)
    print(f"Saved readings to {readings_file}")

    print("Fetching station geographic metadata...")
    req_st = urllib.request.Request(
        stations_url, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req_st) as response:
        stations_data = json.loads(response.read().decode("utf-8"))

    stations_file = output_dir / "raw_stations.json"
    with open(stations_file, "w", encoding="utf-8") as f:
        json.dump(stations_data, f, indent=2)
    print(f"Saved station metadata to {stations_file}")


if __name__ == "__main__":
    fetch_rainfall_data()


    

