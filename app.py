import pandas as pd
import streamlit as st
import pydeck as pdk

st.set_page_config(page_title="Green Hydrogen Locator", layout="wide")
st.title("🌍 Green Hydrogen Projects Viewer")
st.markdown("Search by **country** to view real projects and their technologies from your dataset.")

# Load your Excel file (must match filename in repo)
EXCEL_FILE = "Hydro Database - Final.xlsx"
df = pd.read_excel(EXCEL_FILE)

# Ensure lat/lon are numeric
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df = df.dropna(subset=["Latitude", "Longitude"])

# Search box
query = st.text_input("🔍 Enter a country name (e.g. USA, NLD, FRA):")

if query:
    filtered = df[df["Country"].astype(str).str.contains(query, case=False, na=False)]
    st.success(f"✅ Found {len(filtered)} project(s) in '{query}'.")

    if not filtered.empty:
        # Map
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pdk.ViewState(
                latitude=filtered["Latitude"].mean(),
                longitude=filtered["Longitude"].mean(),
                zoom=4,
                pitch=0
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=filtered,
                    get_position='[Longitude, Latitude]',
                    get_radius=30000,
                    get_color=[0, 120, 200, 160],
                    pickable=True
                )
            ],
            tooltip={
                "html": "<b>Project:</b> {Project Name}<br/>"
                        "<b>Status:</b> {Status}<br/>"
                        "<b>Tech:</b> {Technology}<br/>"
                        "<b>Product:</b> {Product}<br/>"
                        "<b>Size:</b> {Announced Size}",
                "style": {"backgroundColor": "navy", "color": "white"}
            }
        ))

        # Table view
        st.dataframe(filtered.reset_index(drop=True))
    else:
        st.warning("No projects found for that country.")
else:
    st.info("Enter a country to begin.")
