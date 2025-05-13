import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.set_page_config(page_title="Green Hydrogen Locator", layout="wide")
st.title("🌍 Green Hydrogen Projects by Region")
st.markdown("Enter a state, region, or province to find hydrogen projects from the original IEA dataset.")

# Load the Excel file (must be in same directory in GitHub repo)
EXCEL_FILE = "IEA Hydrogen Production Projects Database_update_5_March_202555.xlsx"

# Load headers
df = pd.read_excel(EXCEL_FILE, sheet_name="Projects", header=2)

# Ensure coordinates are clean
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df = df.dropna(subset=["Latitude", "Longitude"])

# Reverse geocode coordinates
geolocator = Nominatim(user_agent="green-h2-locator")
reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

@st.cache_data(show_spinner=True)
def add_region_column(data):
    def get_region(lat, lon):
        try:
            location = reverse((lat, lon), language='en')
            return location.raw.get("address", {}).get("state") or ""
        except:
            return ""
    data["Region"] = data.apply(lambda row: get_region(row["Latitude"], row["Longitude"]), axis=1)
    return data

st.info("Processing coordinates...")
df = add_region_column(df)

# Search bar
query = st.text_input("🔍 Enter a U.S. state, province, or region:")

if query:
    matches = df[df["Region"].str.contains(query, case=False, na=False)]
    st.success(f"✅ Found {len(matches)} projects in or near '{query}'.")

    if not matches.empty:
        result = matches[["Project name", "Status", "Technology", "Announced Size", "Country", "Region"]]
        result.columns = ["Project Name", "Status", "Technology", "Announced Size", "Country", "Region"]
        st.dataframe(result.reset_index(drop=True))
    else:
        st.warning("No matching projects found.")
else:
    st.info("Type a location to search.")
