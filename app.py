import streamlit as st
import os
import pandas as pd
import re
from ocr_extraction import extract_text_from_pdf
from faiss_db import store_ef_value
from gemini_analysis import analyze_with_gemini

# Streamlit UI
st.set_page_config(page_title="EF Value Extractor", layout="centered")
st.title("HF Detector")

uploaded_files = st.file_uploader("📂 Drop Patient Summary Files", type="pdf", accept_multiple_files=True)

def extract_ef_values(text):
    """Extracts EF-related values including LVEF, EF-A2C, EF-A4C, and ranges."""
    ef_pattern = re.compile(r'(LVEF|EF(?:-A2C|-A4C|-Biplane|-PLAX|-PSAX|-Subcostal|-Other|-Global|-Mmode)?)[^\d]*(\d{1,3}(?:\.\d+)?)\s*(?:-|to)?\s*(\d{1,3}(?:\.\d+)?)?\s*[%o/o]?', re.IGNORECASE)
    matches = ef_pattern.findall(text)
    return [(m[0], m[1] if not m[2] else f"{m[1]}-{m[2]}") for m in matches]

def determine_risk(ef_values):
    """Determines patient risk based on EF values (High Risk if any EF <40)."""
    for _, ef_value in ef_values:
        ef_value = ef_value.replace("%", "").strip()
        try:
            if '-' in ef_value:
                low, _ = map(float, ef_value.split('-'))
                if low < 40.0:
                    return "High Risk"
            elif float(ef_value) < 40.0:
                return "High Risk"
        except ValueError:
            continue
    return "Low Risk"

if uploaded_files:
    results = []

    with st.spinner("Processing the uploaded PDFs... Please wait."):
        for uploaded_file in uploaded_files:
            pdf_path = os.path.join("temp_files", uploaded_file.name)
            os.makedirs("temp_files", exist_ok=True)

            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Extract text from PDF (try direct extraction first, then OCR)
            extracted_text = extract_text_from_pdf(pdf_path)

            # Analyze text with Gemini Pro
            ai_analysis = analyze_with_gemini(extracted_text)
            ef_values = extract_ef_values(ai_analysis)

            if not ef_values:
                results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "No EF Value Found"})
            else:
                ef_combined = "; ".join([f"{ef[0]}: {ef[1]}" for ef in ef_values])
                for ef_type, ef_value in ef_values:
                    store_ef_value(extracted_text, ef_value, uploaded_file.name)
                risk_nature = determine_risk(ef_values)
                results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": risk_nature, "EF Values": ef_combined})

    df = pd.DataFrame(results)

    # Define a function to apply conditional formatting
    def highlight_risk(val):
        color = 'red' if val == "High Risk" else 'green' if val == "Low Risk" else 'black'
        return f'color: {color}'

    # Apply conditional formatting and display the DataFrame
    styled_df = df.style.applymap(highlight_risk, subset=['Risk Nature'])
    st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)