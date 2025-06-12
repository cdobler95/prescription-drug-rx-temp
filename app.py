import re
import streamlit as st
import pandas as pd
import io
from fpdf import FPDF

st.title("💊 Prescription Generator")

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

data["label"] = (
    data["drug_name"] + " " + data["dose"] + " (" + data["form"].fillna("") + ", " + data["route"].fillna("") + ")"
)
choice = st.selectbox("Select a medication:", sorted(data["label"]))
drug = data[data["label"] == choice].iloc[0]

st.subheader("👤 Patient Info")
patient_name = st.text_input("Patient Full Name")
patient_dob = st.text_input("Date of Birth (MM/DD/YYYY)")

st.subheader("🩺 Prescriber Info")
provider_name = st.text_input("Prescriber Name")
provider_npi = st.text_input("NPI Number")
provider_dea = st.text_input("DEA Number")

frequencies = [
    "once daily", "twice daily", "every 4 hours", "every 6 hours",
    "every 8 hours", "as needed for pain", "before meals", "before bedtime"
]
selected_frequency = st.selectbox("Select Frequency", frequencies)

st.subheader("📦 Dispensing Info")
auto_calc = st.checkbox("🧮 Auto-calculate quantity based on frequency & days supply")
days_supply = st.number_input("Days Supply", min_value=1, value=10)
if auto_calc:
    freq_map = {
        "once daily": 1, "twice daily": 2, "every 4 hours": 6,
        "every 6 hours": 4, "every 8 hours": 3, "before meals": 3,
        "before bedtime": 1, "as needed for pain": 3
    }
    freq_factor = freq_map.get(selected_frequency, 1)
    quantity = freq_factor * days_supply
else:
    quantity = st.number_input("Quantity to Dispense", min_value=1, value=30)

refills = st.selectbox("Refills", list(range(0, 6)))
daw = st.checkbox("☑️ Dispense as Written (DAW)")
controlled = st.checkbox("⚠️ Controlled Substance")

default_rx = f"""
Patient: {patient_name}
DOB: {patient_dob}

RX: {drug.drug_name} {drug.dose}
Take 1 {drug.form} via {drug.route} {selected_frequency}.

Quantity: {quantity}
Days Supply: {days_supply}
Refills: {refills}
Dispense as Written: {'Yes' if daw else 'No'}
Controlled Substance: {'Yes' if controlled else 'No'}

Prescriber: {provider_name}
NPI: {provider_npi}    DEA: {provider_dea}

______________________
Signature
"""
editable_text = st.text_area("📝 Edit Prescription Text", value=default_rx.strip(), height=300)
st.subheader("✅ Final Prescription")
st.code(editable_text.strip(), language="markdown")

buffer = io.StringIO()
buffer.write(editable_text.strip())
st.download_button("📥 Download TXT", buffer.getvalue(), file_name="prescription.txt")

def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Prescription Form", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Patient: {data['patient_name']}", ln=True)
    pdf.cell(200, 10, f"DOB: {data['dob']}", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, f"RX: {data['drug_name']} {data['dose']}", ln=True)
    pdf.multi_cell(0, 10, f"Sig: Take 1 {data['form']} via {data['route']} {data['frequency']}.")
    pdf.cell(200, 10, f"Quantity: {data['quantity']}", ln=True)
    pdf.cell(200, 10, f"Days Supply: {data['days_supply']}", ln=True)
    pdf.cell(200, 10, f"Refills: {data['refills']}", ln=True)
    pdf.cell(200, 10, f"Dispense as Written: {data['daw']}", ln=True)
    if data['controlled'] == "Yes":
        pdf.set_text_color(220, 50, 50)
        pdf.multi_cell(0, 10, "WARNING: This is a Controlled Substance. Follow federal guidelines.")
        pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.cell(200, 10, f"Prescriber: {data['provider_name']}", ln=True)
    pdf.cell(200, 10, f"NPI: {data['npi']}    DEA: {data['dea']}", ln=True)
    pdf.ln(20)
    pdf.cell(200, 10, "_________________________", ln=True)
    pdf.cell(200, 10, "Signature", ln=True)
    return pdf

if st.button("📄 Generate PDF"):
    rx_pdf = generate_pdf({
        "patient_name": patient_name,
        "dob": patient_dob,
        "drug_name": drug.drug_name,
        "dose": drug.dose,
        "form": drug.form,
        "route": drug.route,
        "frequency": selected_frequency,
        "quantity": quantity,
        "days_supply": days_supply,
        "refills": refills,
        "daw": "Yes" if daw else "No",
        "controlled": "Yes" if controlled else "No",
        "provider_name": provider_name,
        "npi": provider_npi,
        "dea": provider_dea
    })
    pdf_bytes = rx_pdf.output(dest='S').encode('latin1')
    st.download_button(
        label="📥 Download PDF",
        data=pdf_bytes,
        file_name="prescription.pdf",
        mime="application/pdf"
    )
