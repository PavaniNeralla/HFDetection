import streamlit as st
import os
import json
import pandas as pd
from ocr_extraction import extract_text_from_pdf
from gemini_analysis import analyze_with_gemini, parse_gemini_response
from risk_analysis import determine_risk
from process_file import process_uploaded_file

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

# Sidebar for adding new metric thresholds
st.sidebar.header("➕ Add Metric Threshold")

with st.sidebar.form("threshold_form"):
    metric = st.text_input("Enter Metric Name", placeholder="e.g., BMI, EF-A2C, BP")
    condition = st.selectbox("Select Condition", ["greater than", "less than", "between"])
    value = st.number_input("Enter Value", min_value=0, max_value=500, value=50)
    value2 = None
    if condition == "between":
        value2 = st.number_input("Enter Second Value", min_value=0, max_value=500, value=60)

    submitted = st.form_submit_button("Save Threshold")
    if submitted:
        if metric:
            st.session_state["threshold_settings"][metric] = {
                "condition": condition,
                "value": value,
                "value2": value2
            }
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

# File processing logic
uploaded_files = st.file_uploader("📂 Upload Scanned PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    results = []
    os.makedirs("temp_files", exist_ok=True)

    with st.spinner("Processing the uploaded PDFs... Please wait."):
        for uploaded_file in uploaded_files:
            result = process_uploaded_file(uploaded_file, st.session_state["threshold_settings"])
            results.append(result)

    if results:
        df = pd.DataFrame(results)

        def highlight_risk(val):
            color = 'red' if val == "High Risk" else 'green' if val == "Low Risk" else 'black'
            return f'color: {color}'

        styled_df = df.style.map(highlight_risk, subset=['Risk Nature'])
        st.write("### Extracted EF and Additional Metrics")
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No files uploaded or no EF/metric values found.")
