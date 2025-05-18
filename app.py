# app.py ─ streamlined & fixed
# ----------------------------------------
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="Hydrogen Projects Locator", layout="wide")

# -------------------- DATA --------------------
@st.cache_data
def load_df():
    df = pd.read_excel("Hydro Database with places.xlsx", sheet_name="Sheet1")
    df["Location"] = df["Location"].fillna(df["Country"])
    return df.dropna(subset=["Latitude", "Longitude"])

df = load_df()

# ----------------- GEOCODING ------------------
@st.cache_data
def geocode(place: str):
    geo = Nominatim(user_agent="hydrogen_locator")
    try:
        loc = geo.geocode(place, timeout=10)
        return (loc.latitude, loc.longitude) if loc else None
    except Exception:
        return None

# -------------- DISTANCE FILTER ---------------
def within_radius(center, r_miles: int):
    lat0, lon0 = center
    out = []
    for _, row in df.iterrows():
        d = geodesic((lat0, lon0), (row.Latitude, row.Longitude)).miles
        if d <= r_miles:
            rec = row.to_dict()
            rec["Distance (miles)"] = round(d, 1)
            out.append(rec)
    return pd.DataFrame(out).sort_values("Distance (miles)")

# ---------------- INPUT FORM ------------------
with st.sidebar.form("search"):
    st.header("🔍  Search")
    country  = st.text_input("Country *")
    city     = st.text_input("City / State (optional)")
    radius   = st.slider("Radius (miles)", 100, 1000, 500)
    submitted = st.form_submit_button("Search")

st.title("🌍  Hydrogen Projects Locator")

# ------------- RUN SEARCH ONCE ----------------
if submitted:
    query  = f"{city}, {country}" if city else country
    coords = geocode(query)

    if coords is None:
        st.error(f"Location not found: {query}")
        st.stop()

    projects = within_radius(coords, radius)
    if projects.empty:
        st.warning("No projects found inside that radius.")
        st.stop()

    # ---------------- LAYOUT ------------------
    left, right = st.columns([2, 1], gap="small")

    # -------- MAP (left) --------
    with left:
        m = folium.Map(location=coords, zoom_start=6)
        folium.Marker(coords, tooltip=query, icon=folium.Icon(color="red")).add_to(m)
        clust = MarkerCluster().add_to(m)
        for _, r in projects.iterrows():
            folium.Marker(
                [r.Latitude, r.Longitude],
                tooltip=r.Location,
                popup=(f"<b>{r['Project name']}</b><br>"
                       f"{r.Location}<br>Status: {r.Status}<br>"
                       f"Tech: {r.Technology}<br>"
                       f"Product: {r.Product}<br>"
                       f"Size: {r['Announced Size']}<br>"
                       f"Distance: {r['Distance (miles)']} mi")
            ).add_to(clust)
        st_folium(m, width=900, height=500)

    # -------- TABLE (right) -----
    with right:
        st.subheader("📋 Projects")
        st.dataframe(
            projects[["Project name", "Country", "Location", "Status",
                      "Technology", "Product", "Announced Size",
                      "Distance (miles)"]].reset_index(drop=True),
            height=500,
            use_container_width=True
        )
else:
    st.info("Fill the form on the left and press **Search** to see results.")
