import streamlit as st
import os
import json
import pandas as pd
from ocr_extraction import extract_text_from_pdf
from gemini_analysis import analyze_with_gemini
from extract_ef import extract_ef_values, determine_risk

# Load or initialize threshold settings
THRESHOLD_FILE = "threshold_settings.json"

def load_threshold_settings():
    """Load threshold settings from file."""
    if os.path.exists(THRESHOLD_FILE):
        with open(THRESHOLD_FILE, "r") as file:
            return json.load(file)
    return {}

def save_threshold_settings(settings):
    """Save threshold settings without triggering Streamlit reload."""
    with open(THRESHOLD_FILE, "w") as file:
        json.dump(settings, file, indent=4)

# Load settings into session state (to prevent unnecessary reloads)
if "threshold_settings" not in st.session_state:
    st.session_state["threshold_settings"] = load_threshold_settings()

# Streamlit UI
st.set_page_config(page_title="Threshold Settings", layout="wide")
st.title("HF Detector")

# Sidebar for adding new threshold settings
st.sidebar.header("➕ Add Metric Threshold")

with st.sidebar.form("threshold_form"):
    metric = st.text_input("Enter Metric Name", placeholder="e.g., BMI, EF-A2C")
    condition = st.selectbox("Select Condition", ["greater than", "less than", "between"])
    value = st.number_input("Enter Value", min_value=0, max_value=100, value=50)
    value2 = None
    if condition == "between":
        value2 = st.number_input("Enter Second Value", min_value=0, max_value=100, value=60)

    submitted = st.form_submit_button("Save Threshold")
    if submitted:
        if metric:
            st.session_state["threshold_settings"][metric] = {"condition": condition, "value": value, "value2": value2}
            save_threshold_settings(st.session_state["threshold_settings"])
            st.success(f"✅ Threshold for '{metric}' saved successfully!")
        else:
            st.warning("⚠️ Please enter a valid metric name.")

# Display saved threshold settings in an expander in the sidebar
with st.sidebar.expander("📌 Saved Threshold Settings", expanded=False):
    saved_settings = st.session_state["threshold_settings"]
    if saved_settings:
        df = pd.DataFrame.from_dict(saved_settings, orient='index')
        st.dataframe(df)
    else:
        st.write("No saved thresholds yet.")

# File processing logic only runs if new files are uploaded
uploaded_files = st.file_uploader("📂 Upload Scanned PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    results = []
    os.makedirs("temp_files", exist_ok=True)

    with st.spinner("Processing the uploaded PDFs... Please wait."):
        for uploaded_file in uploaded_files:
            try:
                pdf_path = os.path.join("temp_files", uploaded_file.name)
                
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if not os.path.exists(pdf_path):
                    st.error(f"❌ Error: File {pdf_path} was not saved properly.")
                    continue

                extracted_text = extract_text_from_pdf(pdf_path)
                if not extracted_text.strip():
                    st.warning(f"⚠️ No text extracted from {uploaded_file.name}. Skipping.")
                    results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "No EF Value Found"})
                    continue

                ai_analysis = analyze_with_gemini(extracted_text)
                if not ai_analysis.strip():
                    st.warning(f"⚠️ Gemini API did not return a valid response for {uploaded_file.name}. Skipping.")
                    results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "No EF Value Found"})
                    continue

                ef_values, _ = extract_ef_values(ai_analysis)
                ef_values_filtered = {k: v for k, v in ef_values.items() if v not in ["NA", "No EF found"] and any(char.isdigit() for char in v)}

                if ef_values_filtered:
                    risk_nature = determine_risk(ef_values_filtered)
                    ef_combined = "; ".join([f"{key}: {value}" for key, value in ef_values_filtered.items()])
                    
                    # Apply threshold filter
                    saved_thresholds = st.session_state["threshold_settings"]
                    if metric in ef_values_filtered and metric in saved_thresholds:
                        ef_value = float(ef_values_filtered[metric])
                        condition = saved_thresholds[metric]["condition"]
                        value = saved_thresholds[metric]["value"]
                        value2 = saved_thresholds[metric]["value2"]

                        if (condition == "greater than" and ef_value <= value) or \
                           (condition == "less than" and ef_value >= value) or \
                           (condition == "between" and not (value <= ef_value <= value2)):
                            continue
                else:
                    risk_nature = "NA"
                    ef_combined = "No EF Value Found"

                results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": risk_nature, "EF Values": ef_combined})
            except Exception as e:
                st.error(f"❌ Error processing file {uploaded_file.name}: {e}")

    if results:
        df = pd.DataFrame(results)
        
        def highlight_risk(val):
            color = 'red' if val == "High Risk" else 'green' if val == "Low Risk" else 'black'
            return f'color: {color}'
        
        styled_df = df.style.applymap(highlight_risk, subset=['Risk Nature'])
        st.write("### Extracted EF Values")
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No files uploaded or no EF values found.")
