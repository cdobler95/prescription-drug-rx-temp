import re
import streamlit as st
import pandas as pd

st.title("💊 Prescription Generator")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("drugs.csv", encoding="utf-8")
    except:
        df = pd.read_csv("drugs.csv", encoding="ISO-8859-1")

    df = df.rename(columns={
        "brand_name": "drug_name",
        "dosage_form": "form"
    })

    strength_re = re.compile(r"\(([^)]+)\)")
    df["dose"] = (
        df["active_ingredients"]
        .astype(str)
        .str.extract(strength_re, expand=False)
        .fillna("")
        .str.replace(r"\s+", "", regex=True)
    )

    return df[["drug_name", "dose", "form", "route"]].dropna().drop_duplicates()

try:
    data = load_data()
except Exception as e:
    st.error(f"❌ Error loading CSV: {e}")
    st.stop()

data["label"] = (
    data["drug_name"]
    + " " + data["dose"]
    + " (" + data["form"] + ", " + data["route"] + ")"
)

choice = st.selectbox("Select a medication:", sorted(data["label"]))

drug = data[data["label"] == choice].iloc[0]

rx_text = f"""
RX: {drug.drug_name} {drug.dose}
TAKE: 1 {drug.form} via {drug.route} every 6 hours as needed for pain.
"""

st.subheader("📝 Generated Prescription")
st.code(rx_text.strip(), language="markdown")
