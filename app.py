import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from streamlit_cookies_manager import EncryptedCookieManager

st.set_page_config(page_title="Hydrogen Projects Locator", layout="wide")

PASSWORD = "subscriber_pass"
MAX_FREE_USES = 4

# --- COOKIE SETUP ---
cookies = EncryptedCookieManager(prefix="carbonshift_", password="your_cookie_secret")
if not cookies.ready():
    st.stop()

# Initialize persistent values from cookies
if "search_count" not in cookies:
    cookies["search_count"] = "0"
if "unlocked" not in cookies:
    cookies["unlocked"] = "False"

search_count = int(cookies["search_count"])
unlocked = cookies["unlocked"] == "True"

# --- PASSWORD FUNCTION ---
def check_password():
    def verify():
        if st.session_state["password_input"] == PASSWORD:
            cookies["unlocked"] = "True"
            cookies.save()
            st.success("🔓 Successfully unlocked! Unlimited searches enabled.")
        else:
            st.error("❌ Incorrect password. Try again.")

    st.text_input("Subscriber Password:", type="password",
                  key="password_input", on_change=verify)

# --- LOAD DATA ---
@st.cache_data
def load_df():
    df = pd.read_excel("Hydro Database with places.xlsx", sheet_name=0)
    df["Location"] = df["Location"].fillna(df["Country"])
    return df.dropna(subset=["Latitude", "Longitude"])

df = load_df()

# --- GEOCODER ---
geocoder = Nominatim(user_agent="hydrogen_locator")

@st.cache_data
def geocode(place: str):
    loc = geocoder.geocode(place, timeout=10)
    return (loc.latitude, loc.longitude) if loc else None

# --- DISTANCE FILTER ---
def nearby(center, radius_mi: int):
    lat0, lon0 = center
    out = []
    for _, row in df.iterrows():
        d = geodesic((lat0, lon0), (row.Latitude, row.Longitude)).miles
        if d <= radius_mi:
            rec = row.to_dict()
            rec["Distance (miles)"] = round(d, 1)
            out.append(rec)
    return pd.DataFrame(out).sort_values("Distance (miles)")

# --- SIDEBAR FORM ---
with st.sidebar.form("search"):
    st.header("🔍 Search")
    country = st.text_input("Country *")
    city = st.text_input("City / State (optional)")
    radius = st.slider("Radius (miles)", 100, 1000, 500)
    submitted = st.form_submit_button("Search")

st.title("🌍 Hydrogen Projects Locator")

# --- LOCK AFTER MAX_FREE_USES ---
if search_count >= MAX_FREE_USES and not unlocked:
    st.warning(
        "🔒 You've reached your free search limit. "
        "[Subscribe to The Carbon Shift](https://www.thecarbonshift.com/) to unlock unlimited access."
    )
    check_password()
    st.stop()

# --- SEARCH ACTION ---
if submitted:
    search_count += 1
    cookies["search_count"] = str(search_count)
    cookies.save()

    query = f"{city}, {country}" if city else country
    coords = geocode(query)

    if coords is None:
        st.error(f"Location not found: {query}")
    else:
        st.session_state["query"] = query
        st.session_state["coords"] = coords
        st.session_state["results"] = nearby(coords, radius)

# --- DISPLAY RESULTS ---
if "results" in st.session_state and not st.session_state["results"].empty:
    results = st.session_state["results"]
    center = st.session_state["coords"]

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

    with st.container():
        st_folium(m, height=500, use_container_width=True)
        st.subheader("📋 Projects within radius")
        st.dataframe(
            results[["Project name", "Country", "Location", "Status",
                     "Technology", "Product", "Announced Size",
                     "Distance (miles)"]].reset_index(drop=True),
            height=500,
            use_container_width=True
        )
else:
    st.info("Use the form on the left and press **Search**.")

st.sidebar.caption(f"Searches used: {search_count} / {MAX_FREE_USES}")
