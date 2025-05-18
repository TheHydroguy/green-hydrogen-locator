import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="Hydrogen Projects Locator", layout="wide")

# Load data safely
@st.cache_data
def load_data():
    df = pd.read_excel('Hydro Database with places.xlsx', sheet_name='Sheet1')
    df['Location'] = df['Location'].fillna(df['Country'])
    return df.dropna(subset=['Latitude', 'Longitude'])

df = load_data()

# Safe geocoding
@st.cache_data
def get_coords(place):
    geolocator = Nominatim(user_agent="hydrogen_locator")
    try:
        location = geolocator.geocode(place, timeout=10)
        return (location.latitude, location.longitude) if location else None
    except:
        return None

# Filtering function
def find_projects(coords, radius):
    df["Distance (miles)"] = df.apply(lambda row: geodesic(coords, (row.Latitude, row.Longitude)).miles, axis=1)
    return df[df["Distance (miles)"] <= radius].sort_values("Distance (miles)")

# Sidebar form for input (prevents the disappearing problem)
with st.sidebar.form("search_form"):
    st.header("🔍 Project Search")
    country = st.text_input("Country (required)")
    city_state = st.text_input("City or State (optional)")
    radius = st.slider("Radius (miles)", 100, 1000, 500)
    submitted = st.form_submit_button("Search")

st.title("🌍 Hydrogen Projects Locator")

if submitted:
    query = f"{city_state}, {country}" if city_state else country
    coords = get_coords(query)

    if coords:
        filtered_df = find_projects(coords, radius)
        if filtered_df.empty:
            st.warning("No projects found. Increase radius or change location.")
        else:
            # Map Visualization
            m = folium.Map(location=coords, zoom_start=5)
            folium.Marker(coords, tooltip="Your Search Location", icon=folium.Icon(color='red')).add_to(m)
            cluster = MarkerCluster().add_to(m)

            for _, proj in filtered_df.iterrows():
                folium.Marker(
                    location=[proj['Latitude'], proj['Longitude']],
                    popup=(
                        f"<b>{proj['Project name']}</b><br>"
                        f"{proj['Location']}<br>Status: {proj['Status']}<br>"
                        f"Technology: {proj['Technology']}<br>"
                        f"Product: {proj['Product']}<br>"
                        f"Size: {proj['Announced Size']}<br>"
                        f"Distance: {proj['Distance (miles)']:.1f} miles"
                    ),
                    tooltip=proj['Location']
                ).add_to(cluster)

            st_folium(m, width=1100, height=500)

            # Show results table clearly
            st.subheader("📋 Projects within radius:")
            st.dataframe(filtered_df[["Project name", "Country", "Location", "Status",
                                      "Technology", "Product", "Announced Size", "Distance (miles)"]].reset_index(drop=True), width=1100)
    else:
        st.error("Location not found. Please try again.")
else:
    st.info("Fill the form and click 'Search' to display hydrogen projects.")
