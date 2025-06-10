import re
import streamlit as st
import pandas as pd

st.title("💊 Prescription Generator")

# ---------- DATA LOADING ----------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("drugs.csv")  # Try default (UTF-8)
    except UnicodeDecodeError:
        df = pd.read_csv("drugs.csv", encoding="ISO-8859-1")  # Fallback

    # Rename columns
    df = df.rename(columns={"brand_name": "drug_name", "dosage_form": "form"})

    # Extract dose from active_ingredients (e.g., (30MG))
    strength_re = re.compile(r"\(([^)]+)\)")
    df["dose"] = (
        df["active_ingredients"]
        .str.extract(strength_re, expand=False)
        .fillna("")
        .str.replace(r"\s+", "", regex=True)
    )

    # Final clean dataset
    return (
        df[["drug_name", "dose", "form", "route"]]
        .dropna(subset=["drug_name"])
        .drop_duplicates()
        .reset_index(drop=True)
    )

try:
    data = load_data()
except Exception as e:
    st.error(f"❌ Failed to load drugs.csv: {e}")
    st.stop()

# ---------- UI ----------
data["label"] = (
    data["drug_name"]
    + " "
    + data["dose"]
    + " (" + data["form"].fillna("") + ", " + data["route"].fillna("") + ")"
)

choice = st.selectbox("Select a medication:", sorted(data["label"]))

drug = data[data["label"] == choice].iloc[0]

rx_text = f"""
RX: {drug.drug_name} {drug.dose}
TAKE: 1 {drug.form} via {drug.route} every 6 hours as needed for pain.
"""

st.subheader("📝 Generated Prescription")
st.code(rx_text.strip(), language="markdown")