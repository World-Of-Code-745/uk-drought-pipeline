# UK Real-Time Rainfall Monitoring Pipeline

A robust data engineering pipeline that ingests live 15-minute precipitation telemetry from the UK Environment Agency API, enriches spatial metadata, stores snapshots in SQLite, and visualizes active rainfall across England and Wales.

## Architecture

```
[ UK Environment Agency API ]
          │ (REST / JSON)
          ▼
┌──────────────────────────────┐
│  01_ingestion/fetch_data.py  │ ──► Raw JSON (readings & station metadata)
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  02_storage/process_data.py  │ ──► Merges spatial metadata (lat/lon/town)
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  data/processed/rainfall.db  │ ──► SQLite relational database (rainfall_measures)
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 03_visualisation/app.py      │ ──► Interactive Streamlit + Plotly Dashboard
└──────────────────────────────┘
```

## Core Features

* **Live Telemetry Ingestion:** Pulls 15-minute precipitation data from 1,000+ active rain gauge stations.
* **Geographic Enrichment:** Merges station metadata endpoints to append spatial coordinates (`latitude`, `longitude`) and town locations with 99.7% coverage.
* **Outlier-Resilient Visualizations:** Uses a ranked **Plotly Logarithmic Curve Plot** (0.1mm - 20mm+) so trace rainfall amounts remain visually distinct alongside heavy spikes.
* **Interactive Map Focus:** Built-in Streamlit spatial map allowing users to select and isolate individual active rainfall stations across England and Wales.
* **UTC ISO Timestamp Formatting:** Automatically converts ISO 8601 UTC timestamps into localized human-readable date strings.

## Repository Structure

```text
uk-drought-pipeline/
├── .venv/                     # Python virtual environment (bin, include, lib)
├── data/
│   ├── raw/                   # Raw API JSON responses (raw_readings.json, raw_stations.json)
│   └── processed/             # Processed SQLite database (rainfall.db)
├── src/
│   ├── 01_ingestion/          # Ingestion logic (fetch_data.py)
│   ├── 02_storage/            # ETL & SQLite loading logic (process_data.py)
│   └── 03_visualisation/      # Streamlit & Plotly app (app.py)
├── README.md                  # Project documentation
└── requirements.txt           # Environment dependencies (pandas, sqlalchemy, streamlit, plotly)
```

## Database Schema (`rainfall_measures`)

Data is processed and stored in `data/processed/rainfall.db` under the `rainfall_measures` table:

| Column | Type | Description |
| :--- | :--- | :--- |
| `station_id` | TEXT | Unique alphanumeric station reference identifier |
| `town` | TEXT | Associated town or location name |
| `parameter` | TEXT | Telemetry type (`Rainfall`) |
| `unit_name` | TEXT | Measurement unit (`mm`) |
| `qualifier` | TEXT | Measurement qualifier (`Analysis` / `15min`) |
| `value` | REAL | Total recorded precipitation value in millimeters |
| `datetime` | TEXT | Timestamp of reading (ISO 8601 format) |
| `latitude` | REAL | Decimal latitude coordinate |
| `longitude` | REAL | Decimal longitude coordinate |

## Quickstart & Execution Pipeline

### 1. Installation

```bash
# Clone repository
git clone https://github.com/your-username/uk-drought-pipeline.git
cd uk-drought-pipeline

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate

# Install required dependencies
pip install pandas sqlalchemy streamlit plotly
```

### 2. Running the Pipeline

```bash
# Step 1: Ingest live telemetry & station metadata
python src/01_ingestion/fetch_data.py

# Step 2: Process, join spatial coordinates, and load into SQLite
python src/02_storage/process_data.py

# Step 3: Launch interactive Streamlit dashboard
streamlit run src/03_visualisation/app.py
```

## Data Source & Attribution

Data is sourced directly from the **UK Environment Agency Real-Time Flood Monitoring API**:
* API Documentation: `https://environment.data.gov.uk/flood-monitoring/doc/reference`
* Contains public sector information licensed under the [Open Government Licence v3.0](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

