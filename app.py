import re
import streamlit as st
import pandas as pd
import io

st.title("💊 Prescription Generator")

# ---------- DATA LOADING ----------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("drugs.csv")
    except UnicodeDecodeError:
        df = pd.read_csv("drugs.csv", encoding="ISO-8859-1")

    df = df.rename(columns={"brand_name": "drug_name", "dosage_form": "form"})

    strength_re = re.compile(r"\(([^)]+)\)")
    df["dose"] = (
        df["active_ingredients"]
        .str.extract(strength_re, expand=False)
        .fillna("")
        .str.replace(r"\s+", "", regex=True)
    )

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

# ---------- UI: DRUG SELECTION ----------
data["label"] = (
    data["drug_name"]
    + " "
    + data["dose"]
    + " (" + data["form"].fillna("") + ", " + data["route"].fillna("") + ")"
)
choice = st.selectbox("Select a medication:", sorted(data["label"]))
drug = data[data["label"] == choice].iloc[0]

# ---------- UI: PATIENT & PRESCRIBER INFO ----------
st.subheader("👤 Patient Info")
patient_name = st.text_input("Patient Full Name")
patient_dob = st.text_input("Date of Birth (MM/DD/YYYY)")

st.subheader("🩺 Prescriber Info")
provider_name = st.text_input("Prescriber Name")
provider_npi = st.text_input("NPI Number")
provider_dea = st.text_input("DEA Number")

# ---------- FREQUENCY SELECTION ----------
frequencies = [
    "once daily", "twice daily", "every 4 hours", "every 6 hours",
    "every 8 hours", "as needed for pain", "before meals", "before bedtime"
]
selected_frequency = st.selectbox("Select Frequency", frequencies)

# ---------- DEFAULT RX TEMPLATE ----------
default_rx = f"""
Patient: {patient_name}
DOB: {patient_dob}

RX: {drug.drug_name} {drug.dose}
Take 1 {drug.form} via {drug.route} {selected_frequency}.

Prescriber: {provider_name}
NPI: {provider_npi}    DEA: {provider_dea}

______________________
Signature
"""

editable_text = st.text_area("📝 Edit Prescription Text", value=default_rx.strip(), height=250)

# ---------- DISPLAY FINAL OUTPUT ----------
st.subheader("✅ Final Prescription")
st.code(editable_text.strip(), language="markdown")

# ---------- DOWNLOAD ----------
buffer = io.StringIO()
buffer.write(editable_text.strip())
st.download_button("📥 Download Prescription", buffer.getvalue(), file_name="prescription.txt")
