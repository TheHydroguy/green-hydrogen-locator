import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.set_page_config(page_title="Green Hydrogen Projects Locator", layout="wide")
st.title("🌍 Green Hydrogen Projects Locator")
st.markdown("Enter a **state or region name** (e.g. `Texas`, `New York`) to find real green hydrogen projects from the IEA dataset.")

# Load Excel directly (assumes Excel file is in same repo)
EXCEL_FILE = "IEA Hydrogen Production Projects Database_update_5_March_202555.xlsx"

# Load the proper header row
header_row = pd.read_excel(EXCEL_FILE, sheet_name="Projects", header=None).iloc[2].fillna("").astype(str).tolist()
df = pd.read_excel(EXCEL_FILE, sheet_name="Projects", header=3)
df.columns = header_row

# Filter Electrolysis and valid coordinates
df = df[df["Technology_aggregate"] == "Electrolysis"].copy()
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df = df.dropna(subset=["Latitude", "Longitude"])

# Reverse geocode to extract region/state
st.info("Reverse geocoding coordinates... may take a few seconds.")
geolocator = Nominatim(user_agent="green-h2-app")
reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

@st.cache_data(show_spinner=False)
def geocode_regions(df):
    df["Region"] = df.apply(lambda row: reverse((row["Latitude"], row["Longitude"]), language='en').raw.get("address", {}).get("state", ""), axis=1)
    return df

df = geocode_regions(df)

# Search input
query = st.text_input("🔍 Enter a U.S. state, country, or region:")

if query:
    filtered = df[df["Region"].str.contains(query, case=False, na=False)]

    st.success(f"✅ Found {len(filtered)} project(s) in '{query}'.")

    if not filtered.empty:
        display = filtered[["Project name", "Status", "Technology", "Announced Size", "Country", "Region"]]
        display.columns = ["Project Name", "Status", "Technology", "Announced Size (kt H2/y)", "Country", "Region"]
        st.dataframe(display.reset_index(drop=True))
    else:
        st.warning("No matching projects found.")
else:
    st.info("Type a location to search.")
