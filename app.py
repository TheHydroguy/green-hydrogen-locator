import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(layout="wide", page_title="Hydrogen Projects Locator")

# Load data from Excel
@st.cache_data
def load_data():
    df = pd.read_excel('Hydro Database with places.xlsx', sheet_name='Sheet1')
    df['Location'] = df['Location'].fillna(df['Country'])
    return df

df = load_data()

# Geocode input location
@st.cache_data
def geocode_location(query):
    geolocator = Nominatim(user_agent="hydrogen_locator")
    location = geolocator.geocode(query)
    return (location.latitude, location.longitude) if location else None

# Filter projects within radius
def filter_projects(df, coords, radius=500):
    df['Distance (miles)'] = df.apply(lambda row: geodesic(coords, (row.Latitude, row.Longitude)).miles, axis=1)
    return df[df['Distance (miles)'] <= radius].sort_values(by='Distance (miles)')

# Sidebar UI
with st.sidebar:
    st.header("🔎 Search Projects")
    country = st.text_input("Country (required):")
    location = st.text_input("City or State (optional):")
    radius = st.slider("Radius (miles)", 100, 1000, 500)
    search_clicked = st.button("Search")

st.title("🌍 Hydrogen Projects Locator")

if search_clicked:
    query = f"{location}, {country}" if location else country
    coords = geocode_location(query)

    if coords:
        filtered_df = filter_projects(df, coords, radius)

        if filtered_df.empty:
            st.warning("No projects found within the specified radius.")
        else:
            # Map generation
            m = folium.Map(location=coords, zoom_start=6)
            MarkerCluster().add_to(m)
            folium.Marker(coords, icon=folium.Icon(color='red'), tooltip=query).add_to(m)

            for _, row in filtered_df.iterrows():
                folium.Marker(
                    location=[row.Latitude, row.Longitude],
                    popup=(
                        f"<strong>{row['Project name']}</strong><br>"
                        f"Location: {row.Location}<br>"
                        f"Status: {row.Status}<br>"
                        f"Technology: {row.Technology}<br>"
                        f"Product: {row.Product}<br>"
                        f"Size: {row['Announced Size']}<br>"
                        f"Distance: {row['Distance (miles)']:.1f} miles"
                    ),
                    tooltip=row.Location
                ).add_to(m)

            st_folium(m, height=600, width=1200)

            # Table Display
            st.subheader("📋 Projects within radius:")
            st.dataframe(filtered_df[['Project name', 'Country', 'Location', 'Status',
                                      'Technology', 'Product', 'Announced Size', 'Distance (miles)']].reset_index(drop=True), width=1200)
    else:
        st.error("Location not found. Please enter a valid country and/or location.")
else:
    st.info("Enter search criteria and click 'Search' to visualize hydrogen projects.")
