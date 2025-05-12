import pandas as pd
import streamlit as st
import pydeck as pdk

st.set_page_config(page_title="Green Hydrogen Project Locator", layout="wide")
st.title("🌍 Green Hydrogen Project Locator")
st.markdown("Search for **green hydrogen projects** using electrolysis from the IEA database.")

# Load the data
df = pd.read_csv("green_h2_locator_ready.csv")

# Search input
country = st.text_input("Enter a country name to search:")

if country:
    filtered = df[df["Country"].str.contains(country, case=False, na=False)]
    
    if len(filtered) > 0:
        st.success(f"Found {len(filtered)} green hydrogen project(s) in {country.title()}.")
        
        st.map(filtered[["Latitude", "Longitude"]])
        st.dataframe(filtered.reset_index(drop=True))
    else:
        st.warning(f"No green hydrogen projects found in '{country}'.")
else:
    st.info("Enter a country name to begin.")
