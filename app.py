import streamlit as st
import os
import pandas as pd
from ocr_extraction import extract_text_from_pdf
from gemini_analysis import analyze_with_gemini
from extract_ef import extract_ef_values, determine_risk

# Streamlit UI
st.set_page_config(page_title="EF Value Extractor", layout="centered")
st.title("HF Detection")

uploaded_files = st.file_uploader("📂 Upload Scanned PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    results = []
    os.makedirs("temp_files", exist_ok=True)  # Ensure temp_files directory exists

    with st.spinner("Processing the uploaded PDFs... Please wait."):
        for uploaded_file in uploaded_files:
            try:
                pdf_path = os.path.join("temp_files", uploaded_file.name)

                # Save the uploaded file
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                #st.success(f"✅ File saved successfully: {pdf_path}")

                # Ensure the file exists before proceeding
                if not os.path.exists(pdf_path):
                    st.error(f"❌ Error: File {pdf_path} was not saved properly.")
                    continue

                # Extract text from PDF
                extracted_text = extract_text_from_pdf(pdf_path)
                if not extracted_text.strip():
                    st.warning(f"⚠️ No text extracted from {uploaded_file.name}. Skipping.")
                    results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "No EF Value Found"})
                    continue

                # Analyze text with Gemini Pro
                ai_analysis = analyze_with_gemini(extracted_text)
                if not ai_analysis.strip():
                    st.warning(f"⚠️ Gemini API did not return a valid response for {uploaded_file.name}. Skipping.")
                    results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "No EF Value Found"})
                    continue

                # Extract EF values
                ef_values, risk_nature = extract_ef_values(ai_analysis)

                # Determine risk level
                if risk_nature is None:
                    risk_nature = determine_risk(ef_values)

                # Combine EF values for display
                ef_combined = "; ".join([f"{key}: {value}" for key, value in ef_values.items()])
                results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": risk_nature, "EF Values": ef_combined})

            except Exception as e:
                st.error(f"❌ Error processing file {uploaded_file.name}: {e}")

            # No file deletion - keeping for future reference
            #st.info(f"📁 File retained: {pdf_path}")

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
