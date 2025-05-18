import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# Load your Excel data
@st.cache_data
def load_data():
    df = pd.read_excel('Hydro Database with places.xlsx', sheet_name='Sheet1')
    df['Location'] = df['Location'].fillna(df['Country'])
    return df

df = load_data()

# Function to filter projects
def filter_projects(df, country, location):
    if location:
        filtered = df[df['Location'].str.contains(location, case=False, na=False)]
        if not filtered.empty:
            return filtered
    if country:
        filtered = df[df['Country'].str.contains(country, case=False, na=False)]
        if not filtered.empty:
            return filtered
    return df  # Return all if no match

# Streamlit App Interface
st.title("🌍 Hydrogen Projects Locator")

# User inputs
country = st.text_input("Enter Country (e.g., Italy, USA):")
location = st.text_input("Enter City or State (optional):")

# Filter data based on input
filtered_df = filter_projects(df, country, location)

if filtered_df.empty:
    st.warning("No matching projects found. Displaying all available projects.")
    filtered_df = df

# Generate map
map_center = [filtered_df['Latitude'].mean(), filtered_df['Longitude'].mean()]
m = folium.Map(location=map_center, zoom_start=4)
marker_cluster = MarkerCluster().add_to(m)

for _, row in filtered_df.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=(
            f"<b>{row['Project name']}</b><br>"
            f"Status: {row['Status']}<br>"
            f"Technology: {row['Technology']}<br>"
            f"Product: {row['Product']}<br>"
            f"Size: {row['Announced Size']}"
        ),
        tooltip=row['Location']
    ).add_to(marker_cluster)

# Display the map in Streamlit
st_folium(m, width=700, height=500)

# Display data table optionally
with st.expander("📋 See detailed data"):
    st.dataframe(filtered_df[['Project name', 'Country', 'Location', 'Status', 'Technology', 'Product', 'Announced Size']])
