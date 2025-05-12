
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Green Hydrogen Projects Finder", layout="wide")

# Load the dataset
df = pd.read_csv("iea_h2_clean.csv")

st.title("🌍 Green Hydrogen Projects Lookup")
st.markdown("Search for **green hydrogen projects** using electrolysis (from IEA data).")

search = st.text_input("🔎 Enter a country, region, or keyword:")

if search:
    results = df[
        df["Technology Comments"].str.contains(search, case=False, na=False) |
        df["Type of electricity (for electrolysis projects)"].str.contains(search, case=False, na=False)
    ]
    st.success(f"{len(results)} project(s) found.")
    st.dataframe(results)
else:
    st.info("Type a keyword or country to search electrolysis-based hydrogen projects.")
