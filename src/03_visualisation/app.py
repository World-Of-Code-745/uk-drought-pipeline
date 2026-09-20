from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import streamlit as st

st.set_page_config(page_title="UK Real-Time Rainfall Monitoring", layout="wide")


@st.cache_data
def load_data():
    db_path = Path("data/processed/rainfall.db")

    if not db_path.exists():
        st.warning(
            "Database file not found. Please run the data ingestion and processing steps first!"
        )
        return pd.DataFrame()

    engine = create_engine(f"sqlite:///{db_path}")
    df = pd.read_sql("SELECT * FROM rainfall_measures", con=engine)

    df.columns = [col.lower() for col in df.columns]

    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    if "latitude" in df.columns:
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    if "longitude" in df.columns:
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    return df


def format_timestamp(ts_str):
    if not ts_str or pd.isna(ts_str):
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        return str(ts_str)


# --- Main Header ---
st.title("UK Real-Time Rainfall Monitoring Dashboard")
st.markdown(
    "Live 15-minute precipitation telemetry from Environment Agency gauge stations across England and Wales."
)

try:
    df = load_data()

    if df.empty:
        st.info(
            "No data available to display. Ensure your raw JSON files have been processed into SQLite."
        )
    else:
        has_value = "value" in df.columns
        has_station = "station_id" in df.columns

        # --- Display Telemetry Timestamp ---
        if "datetime" in df.columns and not df["datetime"].dropna().empty:
            raw_time = df["datetime"].max()
            formatted_time = format_timestamp(raw_time)
            st.caption(f"📅 **Latest Telemetry Snapshot:** {formatted_time}")
        else:
            st.caption("📅 **Snapshot Window:** Live 15-Minute API Reading")

        # --- Sidebar Filters ---
        st.sidebar.header("Filter Options")
        station_list = (
            sorted(df["station_id"].astype(str).unique().tolist())
            if has_station
            else []
        )
        selected_station = st.sidebar.selectbox(
            "Select Station ID", ["All"] + station_list
        )

        filtered_df = (
            df
            if (selected_station == "All" or not has_station)
            else df[df["station_id"] == selected_station]
        )

        # --- Key Metrics ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Records Displayed", len(filtered_df))
        col2.metric(
            "Unique Stations",
            filtered_df["station_id"].nunique() if has_station else 0,
        )

        max_val = (
            filtered_df["value"].max()
            if (has_value and not filtered_df["value"].dropna().empty)
            else None
        )
        unit_str = (
            filtered_df["unit_name"].iloc[0]
            if ("unit_name" in filtered_df and not filtered_df.empty)
            else "mm"
        )

        col3.metric(
            "Max Recorded Value",
            f"{max_val:.2f} {unit_str}".strip() if max_val is not None else "N/A",
        )

        st.markdown("---")

        # --- Main Visuals Layout ---
        col_chart, col_map = st.columns([1, 1])

        active_rain_df = (
            filtered_df[filtered_df["value"] > 0]
            if has_value
            else pd.DataFrame()
        )

        with col_chart:
            st.subheader("Active Rainfall Telemetry Curve")

            if has_value and has_station and not active_rain_df.empty:
                group_cols = ["station_id"]
                if "town" in active_rain_df.columns:
                    group_cols.append("town")

                # Rank stations by rainfall descending
                top_chart_data = (
                    active_rain_df.groupby(group_cols)["value"]
                    .max()
                    .reset_index()
                    .sort_values(by="value", ascending=False)
                    .head(30)
                )

                # Line + Markers plot sorted by rank
                fig = px.line(
                    top_chart_data,
                    x="station_id",
                    y="value",
                    markers=True,
                    hover_data=["town"] if "town" in top_chart_data.columns else None,
                    labels={
                        "value": "Rainfall (mm)",
                        "station_id": "Station ID",
                        "town": "Town/Location",
                    },
                    title="Ranked Stations (0.1mm - 20mm+ Scaled)",
                )

                # Configure log y-axis with explicit ticks so 0.1mm and 20mm are both clearly distinct
                fig.update_yaxes(
                    type="log",
                    dtick=1,
                    exponentformat="power",
                    gridcolor="rgba(200, 200, 200, 0.2)",
                )

                fig.update_traces(
                    line_color="#1f77b4",
                    line_width=3,
                    marker=dict(size=8, color="#0d47a1"),
                )

                fig.update_layout(
                    xaxis_tickangle=-45,
                    margin=dict(t=30, b=10, l=10, r=10),
                    hovermode="x unified",
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(
                    "No active rainfall (> 0.0 mm) recorded across stations in this snapshot."
                )

        with col_map:
            st.subheader("Gauge Station Map Focus")
            map_data = filtered_df.dropna(subset=["latitude", "longitude"])

            if not map_data.empty:
                active_stations = map_data[map_data["value"] > 0]

                if not active_stations.empty:
                    station_options = ["Show All Stations"] + [
                        f"{row.station_id} ({row.value:.2f} mm)"
                        for _, row in active_stations.sort_values(
                            by="value", ascending=False
                        ).iterrows()
                    ]
                    selected_map_station = st.selectbox(
                        "📍 Highlight Active Station on Map:", station_options
                    )

                    if selected_map_station != "Show All Stations":
                        target_id = selected_map_station.split(" ")[0]
                        map_data = map_data[map_data["station_id"] == target_id]

                st.map(
                    map_data[["latitude", "longitude"]],
                    use_container_width=True,
                )
            else:
                st.info("No spatial coordinate data available to map.")

        st.markdown("---")
        st.subheader("Filtered Dataset")
        st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard: {e}") 