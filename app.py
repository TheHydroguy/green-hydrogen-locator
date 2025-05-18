import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel('Hydro Database with places.xlsx')
    df['Location'] = df['Location'].fillna(df['Country'])
    return df

df = load_data()

# Function to geocode location
@st.cache_data
def get_coords(place):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(place)
    return (location.latitude, location.longitude) if location else None

# Filter projects by distance
def filter_by_distance(df, coords, radius):
    df["Distance (miles)"] = df.apply(lambda row: geodesic(coords, (row["Latitude"], row["Longitude"])).miles, axis=1)
    return df[df["Distance (miles)"] <= radius].sort_values("Distance (miles)")

# Sidebar for input
with st.sidebar:
    st.title("🔍 Hydrogen Project Search")
    country = st.text_input("Country (required)")
    location = st.text_input("City or State (optional)")
    radius = st.slider("Radius (miles)", 100, 1000, 500)
    search = st.button("Search")

st.title("🌎 Hydrogen Projects Locator")

if search:
    query = f"{location}, {country}" if location else country
    coords = get_coords(query)

    if coords:
        filtered_df = filter_by_distance(df, coords, radius)
        if filtered_df.empty:
            st.warning("No projects found within this radius. Try increasing the radius or changing the location.")
        else:
            # Generate Map
            m = folium.Map(location=coords, zoom_start=6)
            folium.Marker(coords, icon=folium.Icon(color="red"), tooltip=query).add_to(m)
            marker_cluster = MarkerCluster().add_to(m)
            
            for idx, row in filtered_df.iterrows():
                folium.Marker(
                    [row["Latitude"], row["Longitude"]],
                    popup=f"<b>{row['Project name']}</b><br>{row['Location']}<br>{row['Status']}<br>{row['Technology']}<br>{row['Product']}<br>Size: {row['Announced Size']}<br>{row['Distance (miles)']:.1f} miles away",
                    tooltip=row["Location"]
                ).add_to(marker_cluster)

            st_folium(m, width=1100, height=500)

            # Immediately display table
            st.subheader("📋 Projects found:")
            st.dataframe(filtered_df[["Project name", "Country", "Location", "Status", "Technology", "Product", "Announced Size", "Distance (miles)"]].reset_index(drop=True), width=1100)
    else:
        st.error("Could not find this location. Please check your input.")
else:
    st.info("Enter search criteria and click 'Search' to display hydrogen projects.")
