import streamlit as st
import os
import json
import pandas as pd
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
st.set_page_config(page_title="HF Detector", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
        /* Center the title */
        .css-1n5p33s {
            text-align: center;
        }
        
        /* Hide stop and deploy options */
        .css-1irwz68, .css-1i5ow7f, .css-16xt4j7 {
            visibility: hidden;
        }

        /* Customize button styling */
        .stButton>button {
            width: 100%;
            margin-bottom: 8px;
            border: none;
            background-color: #444; /* Dark background (adjust as needed) */
            color: white;
            font-size: 16px;
            text-align: center;
            border-radius: 5px;
            padding: 10px;
        }
        .stButton>button:hover {
            background-color: #444;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Center the title
st.title("HF Detector 🩺")

# File upload section in the sidebar
st.sidebar.title("Menu")
uploaded_files = st.sidebar.file_uploader("Upload Patient Reports", type="pdf", accept_multiple_files=True)

# When "Extract EF & Metrics" button is clicked, start processing
if st.sidebar.button("Extract EF & Metrics"):
    if uploaded_files:
        # Initialize results and process files
        results = []
        os.makedirs("temp_files", exist_ok=True)

        with st.spinner("Processing the uploaded PDFs... Please wait."):
            for uploaded_file in uploaded_files:
                result = process_uploaded_file(uploaded_file, st.session_state["threshold_settings"])
                results.append(result)

        if results:
            # Display extracted results
            df = pd.DataFrame(results)

            # Drop the "Serial No" column to hide it
            if 'Serial No' in df.columns:
                df = df.drop(columns=['Serial No'])

            def highlight_risk(val):
                color = 'red' if val == "High Risk" else 'green' if val == "Low Risk" else 'black'
                return f'color: {color}'

            styled_df = df.style.map(highlight_risk, subset=['Risk Nature'])
            st.write("### Extracted EF and Additional Metrics")
            st.dataframe(styled_df, use_container_width=True)

        else:
            st.info("No files uploaded or no EF/metric values found.")
    else:
        st.error("Please upload at least one PDF file to extract EF and metrics.")

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
with st.sidebar.expander("📌 Saved Threshold Metrics", expanded=False):
    saved_settings = st.session_state["threshold_settings"]
    if saved_settings:
        df = pd.DataFrame.from_dict(saved_settings, orient='index')
        st.dataframe(df)
    else:
        st.write("No saved thresholds yet.")

