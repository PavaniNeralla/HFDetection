import streamlit as st
import os
import pandas as pd
from ocr_extraction import extract_text_from_pdf
from gemini_analysis import analyze_with_gemini

# Streamlit UI
st.set_page_config(page_title="EF Value Extractor", layout="centered")
st.title("HF Detection")

uploaded_files = st.file_uploader("📂 Upload Scanned PDFs", type="pdf", accept_multiple_files=True)

def extract_ef_values(text):
    """Extracts EF-related values including LVEF, EF-A2C, EF-A4C, and others."""
    ef_values = []
    lines = text.split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().split()[0]  # Get the first part of the value
            if value.endswith('%'):
                value = value[:-1]
            try:
                value = float(value)
                ef_values.append((key, value))
            except ValueError:
                continue
    return ef_values

def determine_risk(ef_values):
    """Determines patient risk based on EF values (High Risk if any EF <40)."""
    for _, ef_value in ef_values:
        if ef_value < 40.0:
            return "High Risk"
    return "Low Risk"

if uploaded_files:
    results = []

    with st.spinner("Processing the uploaded PDFs... Please wait."):
        for uploaded_file in uploaded_files:
            try:
                pdf_path = os.path.join("temp_files", uploaded_file.name)
                os.makedirs("temp_files", exist_ok=True)

                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Extract text from PDF (try direct extraction first, then OCR)
                extracted_text = extract_text_from_pdf(pdf_path)
                st.write(f"Extracted Text: {extracted_text}")  # Debugging information

                # Analyze text with Gemini Pro
                ai_analysis = analyze_with_gemini(extracted_text)
                st.write(f"AI Analysis: {ai_analysis}")  # Debugging information
                ef_values = extract_ef_values(ai_analysis)
                st.write(f"Extracted EF Values: {ef_values}")  # Debugging information

                if not ef_values:
                    results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "No EF Value Found"})
                else:
                    ef_combined = "; ".join([f"{ef[0]}: {ef[1]}%" for ef in ef_values])
                    risk_nature = determine_risk(ef_values)
                    results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": risk_nature, "EF Values": ef_combined})

            except Exception as e:
                st.error(f"Error processing file {uploaded_file.name}: {e}")
            finally:
                # Clean up temporary files
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)

    if results:
        df = pd.DataFrame(results)

        # Define a function to apply conditional formatting
        def highlight_risk(val):
            color = 'red' if val == "High Risk" else 'green' if val == "Low Risk" else 'black'
            return f'color: {color}'

        # Apply conditional formatting
        styled_df = df.style.applymap(highlight_risk, subset=['Risk Nature'])

        st.write("### Extracted EF Values")
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No files uploaded or no EF values found.")
