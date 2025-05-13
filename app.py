import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.set_page_config(page_title="Green Hydrogen Projects Locator", layout="wide")
st.title("🌍 Green Hydrogen Projects Locator")
st.markdown("Enter a **state or region name** (e.g. `Texas`, `New York`) to find real green hydrogen projects from the IEA dataset.")

EXCEL_FILE = "IEA Hydrogen Production Projects Database_update_5_March_202555.xlsx"

# Load data
df = pd.read_excel(EXCEL_FILE, sheet_name="Projects", header=2)

# Clean coordinates
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df = df.dropna(subset=["Latitude", "Longitude"])

# Geocode
st.info("Reverse geocoding project locations...")
geolocator = Nominatim(user_agent="green-h2-locator")
reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

@st.cache_data(show_spinner=False)
def add_region_column(df):
    df["Region"] = df.apply(lambda row: reverse((row["Latitude"], row["Longitude"]), language='en').raw.get("address", {}).get("state", ""), axis=1)
    return df

df = add_region_column(df)

# User search
query = st.text_input("🔍 Enter a region or state name:")

if query:
    matched = df[df["Region"].str.contains(query, case=False, na=False)]

    st.success(f"✅ Found {len(matched)} project(s) matching '{query}'.")

    if not matched.empty:
        result = matched[["Project name", "Status", "Technology", "Announced Size", "Country", "Region"]]
        result.columns = ["Project Name", "Status", "Technology", "Announced Size", "Country", "Region"]
        st.dataframe(result.reset_index(drop=True))
    else:
        st.warning("No matching projects found.")
else:
    st.info("Type a region to search.")
