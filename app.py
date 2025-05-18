# app.py  –  final layout-fix version
# -----------------------------------
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="Hydrogen Projects Locator", layout="wide")

# --- tiny CSS tweak to kill Streamlit’s default big gaps ------------
st.markdown(
    """
    <style>
    .block-container > div + div { margin-top: 0.3rem !important; }
    .block-container { padding-top: 1rem !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- LOAD DATA ----------------------------------------
@st.cache_data
def load_df():
    df = pd.read_excel("Hydro Database with places.xlsx", sheet_name=0)
    df["Location"] = df["Location"].fillna(df["Country"])
    return df.dropna(subset=["Latitude", "Longitude"])

df = load_df()

# ---------------- GEOCODER -----------------------------------------
geocoder = Nominatim(user_agent="hydrogen_locator")

@st.cache_data
def geocode(place: str):
    loc = geocoder.geocode(place, timeout=10)
    return (loc.latitude, loc.longitude) if loc else None

# -------------- DISTANCE FILTER ------------------------------------
def nearby(center, r_miles: int):
    lat0, lon0 = center
    out = []
    for _, row in df.iterrows():
        d = geodesic((lat0, lon0), (row.Latitude, row.Longitude)).miles
        if d <= r_miles:
            rec = row.to_dict()
            rec["Distance (miles)"] = round(d, 1)
            out.append(rec)
    return pd.DataFrame(out).sort_values("Distance (miles)")

# -------------- SIDEBAR SEARCH FORM --------------------------------
with st.sidebar.form("search"):
    st.header("🔎  Search")
    country  = st.text_input("Country *")
    city     = st.text_input("City / State (optional)")
    radius   = st.slider("Radius (miles)", 100, 1000, 500)
    submitted = st.form_submit_button("Search")

st.title("🌍  Hydrogen Projects Locator")

# ---------------- RUN SEARCH & STORE IN SESSION --------------------
if submitted:
    query  = f"{city}, {country}" if city else country
    coords = geocode(query)

    if coords is None:
        st.error(f"Location not found: {query}")
    else:
        st.session_state["query"]   = query
        st.session_state["coords"]  = coords
        st.session_state["results"] = nearby(coords, radius)

# ---------------- DISPLAY SAVED RESULTS ----------------------------
if "results" in st.session_state and not st.session_state["results"].empty:
    results = st.session_state["results"]
    center  = st.session_state["coords"]

    # build map
    m = folium.Map(location=center, zoom_start=6)
    folium.Marker(center, tooltip=st.session_state["query"],
                  icon=folium.Icon(color="red")).add_to(m)
    cluster = MarkerCluster().add_to(m)
    for _, r in results.iterrows():
        folium.Marker(
            [r.Latitude, r.Longitude],
            tooltip=r.Location,
            popup=(f"<b>{r['Project name']}</b><br>"
                   f"{r.Location}<br>Status: {r.Status}<br>"
                   f"Tech: {r.Technology}<br>"
                   f"Product: {r.Product}<br>"
                   f"Size: {r['Announced Size']}<br>"
                   f"Distance: {r['Distance (miles)']} mi")
        ).add_to(cluster)

    # place map and table side-by-side (no vertical gap)
    col_map, col_tbl = st.columns([2, 1], gap="small")
    with col_map:
        st_folium(m, height=500, width=900)
    with col_tbl:
        st.subheader("📋 Projects")
        st.dataframe(
            results[["Project name", "Country", "Location", "Status",
                     "Technology", "Product", "Announced Size",
                     "Distance (miles)"]].reset_index(drop=True),
            height=500,
            use_container_width=True
        )
else:
    st.info("Use the form on the left and press **Search**.")
