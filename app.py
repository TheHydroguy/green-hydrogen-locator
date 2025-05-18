import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="Hydrogen Projects Locator", layout="wide")

# ---------- 1. LOAD DATA -------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("Hydro Database with places.xlsx", sheet_name="Sheet1")
    df["Location"] = df["Location"].fillna(df["Country"])
    return df.dropna(subset=["Latitude", "Longitude"])

df = load_data()

# ---------- 2. GEOCODER (cached) -----------------------------------------
@st.cache_data
def geocode(place: str):
    geo = Nominatim(user_agent="hydrogen_locator")
    try:
        loc = geo.geocode(place, timeout=10)
        return (loc.latitude, loc.longitude) if loc else None
    except Exception:
        return None

# ---------- 3. DISTANCE FILTER -------------------------------------------
def within_radius(lat_lon, r):
    lat0, lon0 = lat_lon
    out = []
    for _, row in df.iterrows():
        d = geodesic((lat0, lon0), (row.Latitude, row.Longitude)).miles
        if d <= r:
            row_dict = row.to_dict()
            row_dict["Distance (miles)"] = round(d, 1)
            out.append(row_dict)
    return pd.DataFrame(out).sort_values("Distance (miles)")

# ---------- 4. SIDEBAR INPUT FORM ----------------------------------------
with st.sidebar.form("search"):
    st.header("🔎  Search Projects")
    country  = st.text_input("Country *")
    city     = st.text_input("City / State (optional)")
    radius   = st.slider("Radius (miles)", 100, 1000, 500)
    submitted = st.form_submit_button("Search")

# ---------- 5. PROCESS INPUT ONCE & SAVE IN SESSION ----------------------
if submitted:
    query = f"{city}, {country}" if city else country
    coords = geocode(query)
    if coords is None:
        st.session_state["error"] = f"❌ Location not found: {query}"
        st.session_state.pop("results", None)
    else:
        st.session_state.pop("error", None)
        st.session_state["query"]   = query
        st.session_state["coords"]  = coords
        st.session_state["results"] = within_radius(coords, radius)

# ---------- 6. MAIN DISPLAY ----------------------------------------------
st.title("🌍  Hydrogen Projects Locator")

# -- error message?
if "error" in st.session_state:
    st.error(st.session_state["error"])

# -- results available?
if "results" in st.session_state and not st.session_state["results"].empty:
    results_df = st.session_state["results"]
    center_lat, center_lon = st.session_state["coords"]

    # map
    m = folium.Map(location=(center_lat, center_lon), zoom_start=6)
    folium.Marker((center_lat, center_lon),
                  tooltip=f"Search: {st.session_state['query']}",
                  icon=folium.Icon(color="red")
                  ).add_to(m)
    cluster = MarkerCluster().add_to(m)
    for _, r in results_df.iterrows():
        folium.Marker(
            location=[r.Latitude, r.Longitude],
            tooltip=r.Location,
            popup=(f"<b>{r['Project name']}</b><br>"
                   f"{r.Location}<br>"
                   f"Status: {r.Status}<br>"
                   f"Tech: {r.Technology}<br>"
                   f"Product: {r.Product}<br>"
                   f"Size: {r['Announced Size']}<br>"
                   f"Distance: {r['Distance (miles)']} mi")
        ).add_to(cluster)

    st_folium(m, width=1100, height=500)

    # table
    st.subheader("📋  Projects within radius")
    st.dataframe(
        results_df[["Project name", "Country", "Location", "Status",
                    "Technology", "Product", "Announced Size",
                    "Distance (miles)"]].reset_index(drop=True),
        use_container_width=True
    )

elif "results" in st.session_state:      # empty search result
    st.warning("No projects found inside that radius. Try a bigger radius or another place.")
else:
    st.info("Fill in the form on the left and press **Search**.")
