import pandas as pd
import streamlit as st

st.set_page_config(page_title="Green Hydrogen Projects (IEA)", layout="wide")
st.title("🌍 Green Hydrogen Projects Viewer (IEA)")
st.markdown("Search by **country, project name, or status** from the official IEA dataset. Fast. No delays.")

# Load the Excel file
EXCEL_FILE = "IEA Hydrogen Production Projects Database_update_5_March_202555.xlsx"
df = pd.read_excel(EXCEL_FILE, sheet_name="Projects", header=2)

# Clean coordinates
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df = df.dropna(subset=["Latitude", "Longitude"])

# Search input
query = st.text_input("🔍 Enter a keyword (project, country, or status):")

if query:
    filtered = df[
        df["Project name"].astype(str).str.contains(query, case=False, na=False) |
        df["Country"].astype(str).str.contains(query, case=False, na=False) |
        df["Status"].astype(str).str.contains(query, case=False, na=False)
    ]
    st.success(f"✅ Found {len(filtered)} matching project(s).")

    if not filtered.empty:
        result = filtered[[
            "Project name", "Status", "Technology", "Announced Size", "Country", "Latitude", "Longitude"
        ]].copy()
        result.columns = [
            "Project Name", "Status", "Technology", "Announced Size", "Country", "Latitude", "Longitude"
        ]
        st.dataframe(result.reset_index(drop=True))
    else:
        st.warning("No matching projects found.")
else:
    st.info("Type a project name, status, or country to begin.")
