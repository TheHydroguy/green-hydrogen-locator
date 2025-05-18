import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="Hydrogen Projects Locator", layout="wide")

# Load data reliably
@st.cache_data
def load_data():
    df = pd.read_excel('Hydro Database with places.xlsx', sheet_name='Sheet1')
    df['Location'] = df['Location'].fillna(df['Country'])
    df = df.dropna(subset=['Latitude', 'Longitude'])
    return df

df = load_data()

# Geocode safely
@st.cache_data
def get_coords(place):
    geolocator = Nominatim(user_agent="hydrogen_locator_app")
    try:
        location = geolocator.geocode(place, timeout=10)
        return (location.latitude, location.longitude) if location else None
    except:
        return None

# Find projects nearby
def find_projects(coords, radius):
    nearby = []
    for idx, row in df.iterrows():
        dist = geodesic(coords, (row['Latitude'], row['Longitude'])).miles
        if dist <= radius:
            row_dict = row.to_dict()
            row_dict['Distance (miles)'] = round(dist, 1)
            nearby.append(row_dict)
    return pd.DataFrame(nearby).sort_values(by='Distance (miles)')

# Sidebar input
with st.sidebar:
    st.title("🔎 Project Search")
    country = st.text_input("Country (required)")
    city_state = st.text_input("City or State (optional)")
    radius = st.slider("Radius (miles)", 100, 1000, 500)
    search = st.button("🔍 Search")

st.title("🌍 Hydrogen Projects Locator")

if search:
    query = f"{city_state}, {country}" if city_state else country
    coords = get_coords(query)

    if coords:
        projects_df = find_projects(coords, radius)

        if projects_df.empty:
            st.warning("No projects found within the specified radius. Expand your radius or adjust your location.")
        else:
            # Generate Map
            map_ = folium.Map(location=coords, zoom_start=5)
            folium.Marker(coords, tooltip="Your Location", icon=folium.Icon(color='red')).add_to(map_)
            cluster = MarkerCluster().add_to(map_)

            for _, proj in projects_df.iterrows():
                folium.Marker(
                    location=[proj['Latitude'], proj['Longitude']],
                    popup=(f"<b>{proj['Project name']}</b><br>"
                           f"Location: {proj['Location']}<br>"
                           f"Status: {proj['Status']}<br>"
                           f"Tech: {proj['Technology']}<br>"
                           f"Product: {proj['Product']}<br>"
                           f"Size: {proj['Announced Size']}<br>"
                           f"Distance: {proj['Distance (miles)']} miles"),
                    tooltip=proj['Location']
                ).add_to(cluster)

            st_folium(map_, height=500, width=1100)

            # Immediately below the map: Projects table
            st.subheader("📋 Projects Found:")
            st.dataframe(projects_df[['Project name', 'Country', 'Location', 'Status', 'Technology',
                                      'Product', 'Announced Size', 'Distance (miles)']].reset_index(drop=True), width=1100)
    else:
        st.error("Unable to find location. Check spelling or try a different location.")
else:
    st.info("Enter location details in sidebar and click '🔍 Search'.")

