import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

# Load your Excel data
@st.cache_data
def load_data():
    df = pd.read_excel('Hydro Database with places.xlsx', sheet_name='Sheet1')
    df['Location'] = df['Location'].fillna(df['Country'])
    return df

df = load_data()

# Geolocate input location
@st.cache_data
def geolocate(place):
    geolocator = Nominatim(user_agent="streamlit_app")
    location = geolocator.geocode(place)
    if location:
        return (location.latitude, location.longitude)
    return None

# Filter projects within radius
def projects_within_radius(df, center, radius_miles=500):
    results = []
    for _, row in df.iterrows():
        proj_location = (row['Latitude'], row['Longitude'])
        distance = geodesic(center, proj_location).miles
        if distance <= radius_miles:
            results.append((row, round(distance, 1)))
    results_df = pd.DataFrame([{
        'Project name': r[0]['Project name'],
        'Country': r[0]['Country'],
        'Location': r[0]['Location'],
        'Status': r[0]['Status'],
        'Technology': r[0]['Technology'],
        'Product': r[0]['Product'],
        'Announced Size': r[0]['Announced Size'],
        'Distance (miles)': r[1]
    } for r in results])
    return results_df

# Streamlit UI
st.title("🌍 Hydrogen Projects Locator (500-mile Radius)")

location_input = st.text_input("📍 Enter City, State, or Country (e.g., Milan, Italy or Houston, Texas):")

if location_input:
    center_coords = geolocate(location_input)

    if center_coords:
        filtered_df = projects_within_radius(df, center_coords)

        if filtered_df.empty:
            st.warning("No projects found within 500 miles.")
        else:
            # Create map
            m = folium.Map(location=center_coords, zoom_start=5)
            folium.Marker(center_coords, tooltip="Search Location", icon=folium.Icon(color='red')).add_to(m)
            marker_cluster = MarkerCluster().add_to(m)

            for _, row in filtered_df.iterrows():
                folium.Marker(
                    location=[df.loc[df['Project name'] == row['Project name'], 'Latitude'].values[0],
                              df.loc[df['Project name'] == row['Project name'], 'Longitude'].values[0]],
                    popup=(f"<b>{row['Project name']}</b><br>"
                           f"Status: {row['Status']}<br>"
                           f"Technology: {row['Technology']}<br>"
                           f"Product: {row['Product']}<br>"
                           f"Size: {row['Announced Size']}<br>"
                           f"Distance: {row['Distance (miles)']} miles"),
                    tooltip=row['Location']
                ).add_to(marker_cluster)

            # Display map
            st_folium(m, width=700, height=500)

            # Display data table
            st.subheader("📋 Projects within 500 miles:")
            st.dataframe(filtered_df.sort_values(by='Distance (miles)'))

    else:
        st.error("Location not found. Please enter a valid location.")
else:
    st.info("Enter a location above to search for nearby hydrogen projects.")
