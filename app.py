import streamlit as st
import pandas as pd
import traceback
from pathlib import Path

# Optional imports wrapped in try/except so we can catch issues
try:
    import folium
    from folium.plugins import MarkerCluster
    from streamlit_folium import st_folium
except Exception as e:
    st.error("❌ Folium import failed:\n" + traceback.format_exc())
    st.stop()

try:
    from geopy.geocoders import Nominatim
    from geopy.distance import geodesic
except Exception as e:
    st.error("❌ geopy import failed:\n" + traceback.format_exc())
    st.stop()

st.set_page_config(page_title="Hydrogen Projects Locator", layout="wide")

# ---------- 1. LOAD DATA (catch errors) ------------
excel_path = Path("Hydro Database with places.xlsx")
if not excel_path.exists():
    st.error(f"❌ Excel file not found: {excel_path.resolve()}")
    st.stop()

try:
    xl = pd.ExcelFile(excel_path)
    sheet = xl.sheet_names[0]           # use first sheet automatically
    df = xl.parse(sheet)
except Exception:
    st.error("❌ Could not read Excel file:\n" + traceback.format_exc())
    st.stop()

if not {"Latitude", "Longitude"}.issubset(df.columns):
    st.error("❌ Excel must contain 'Latitude' and 'Longitude' columns.")
    st.stop()

df["Location"] = df["Location"].fillna(df["Country"])
df = df.dropna(subset=["Latitude", "Longitude"])

# ---------- 2. SAFE GEOCODER ------------------------
geocoder = Nominatim(user_agent="hydrogen_locator")

def geocode(place: str):
    try:
        loc = geocoder.geocode(place, timeout=10)
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception:
        pass
    return None

# ---------- 3. DISTANCE FILTER ----------------------
def within_radius(center, r):
    lat0, lon0 = center
    out = []
    for _, row in df.iterrows():
        try:
            d = geodesic((lat0, lon0), (row.Latitude, row.Longitude)).miles
        except Exception:
            continue
        if d <= r:
            rec = row.to_dict()
            rec["Distance (miles)"] = round(d, 1)
            out.append(rec)
    return pd.DataFrame(out).sort_values("Distance (miles)")

# ---------- 4. SIDEBAR FORM -------------------------
with st.sidebar.form("search"):
    st.header("🔍  Search")
    country  = st.text_input("Country *")
    city     = st.text_input("City / State (optional)")
    radius   = st.slider("Radius (miles)", 100, 1000, 500)
    submitted = st.form_submit_button("Search")

st.title("🌍  Hydrogen Projects Locator")

# ---------- 5. RUN SEARCH ---------------------------
if submitted:
    query  = f"{city}, {country}" if city else country
    coords = geocode(query)

    if coords is None:
        st.error(f"❌ Location not found or geocoder failed for: {query}")
        st.stop()

    results = within_radius(coords, radius)
    if results.empty:
        st.warning("No projects found inside that radius.")
        st.stop()

    # ---------- 6. MAP + TABLE SIDE-BY-SIDE ----------
    try:
        m = folium.Map(location=coords, zoom_start=6)
        folium.Marker(coords, tooltip=query,
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
    except Exception:
        st.error("❌ Error while building map/table:\n" + traceback.format_exc())
