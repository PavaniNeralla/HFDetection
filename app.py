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
st.set_page_config(page_title="Heart Failure Detector", layout="wide", initial_sidebar_state="expanded")
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
        df = df.sort_values(
            by="Risk Nature",
            ascending=False,
            key=lambda col: col.str.contains("High Risk").astype(int)
        )

        # Drop the "Serial No" column to hide it
        if 'Serial No' in df.columns:
            df = df.drop(columns=['Serial No'])

        # Function to create expandable HTML content for EF Values
        def make_expandable_ef_html(values):
            try:
                # Split EF values based on the delimiter (e.g., '; ') and format them as a list
                ef_values_html = "".join(f"<li><b>{item.split(':')[0].strip()}</b>: {item.split(':')[1].strip()}</li>"
                                        for item in values.split(';') if ':' in item)
                html = f"""
                <details>
                <summary>View Metrics</summary>
                <ul>
                    {ef_values_html}
                </ul>
                </details>
                """
                return html.replace("\n", "")  # Return clean, expandable HTML
            except Exception:
                return values  # Return original values if there's an error

        # Apply the function to the EF Values column (if it exists)
        if "EF Values" in df.columns:
            df["EF Values"] = df["EF Values"].apply(make_expandable_ef_html)

        # Add color for "Risk Nature" column
        def color_risk(risk):
            if risk == "High Risk":
                return f"<span style='color: red;'>{risk}</span>"
            elif risk == "Low Risk":
                return f"<span style='color: green;'>{risk}</span>"
            else:
                return risk  # Default for other risk levels

        # Apply the color formatting to the "Risk Nature" column
        if "Risk Nature" in df.columns:
            df["Risk Nature"] = df["Risk Nature"].apply(color_risk)

        # Convert the DataFrame to an HTML table for rendering
        table_html = df.to_html(escape=False, index=False)

        # Use a wider container for better use of screen space
        with st.container():
            st.write("### Extracted EF and Additional Metrics")
            st.markdown(
                """
                <style>
                table {
                    width: 100%; /* Use full width of the container */
                    border-collapse: separate; /* Separate borders for better visuals */
                    border-spacing: 0; /* Remove extra spacing between cells */
                    border: 1px solid #ddd; /* Add a soft border around the table */
                    border-radius: 12px; /* Smooth, rounded corners */
                    overflow: hidden; /* Clip content inside rounded corners */
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Subtle shadow for depth */
                }
                th {
                    text-align: center; /* Horizontal center alignment for headers */
                    vertical-align: middle; /* Vertical center alignment for headers */
                    padding: 12px; /* Add padding for better spacing */
                    background-color: #f9f9f9; /* Light background for headers */
                    border-bottom: 1px solid #ddd; /* Border separating headers */
                    font-weight: bold; /* Make headers bold for clarity */
                }
                td {
                    text-align: left; /* Align cell content to the left */
                    padding: 12px; /* Add consistent padding */
                    border-bottom: 1px solid #ddd; /* Border between rows */
                }
                tr:last-child td {
                    border-bottom: none; /* Remove bottom border for the last row */
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.markdown(table_html, unsafe_allow_html=True)

    else:
        st.info("No files uploaded or no EF/metric values found.")

st.sidebar.header("➕ Add Metric Threshold")

metric = st.sidebar.text_input("Enter Metric Name", placeholder="e.g., BMI, EF-A2C, BP")
condition = st.sidebar.selectbox("Select Condition", ["greater than", "less than", "between"])
value = st.sidebar.number_input("Enter Value", min_value=0, max_value=500, value=50)
value2 = None
if condition == "between":
    value2 = st.sidebar.number_input("Enter Second Value", min_value=0, max_value=500, value=60)
# Sidebar button for saving thresholds
if st.sidebar.button("Save Threshold"):
    if metric:
        st.session_state["threshold_settings"][metric] = {
            "condition": condition,
            "value": value,
            "value2": value2
        }
        save_threshold_settings(st.session_state["threshold_settings"])
        st.sidebar.success(f"Threshold for '{metric}' saved successfully!")
    else:
        st.sidebar.warning("Please enter a valid metric name.")

# Display saved threshold settings in an expander in the sidebar
with st.sidebar.expander("📌 Saved Threshold Metrics", expanded=False):
    saved_settings = st.session_state["threshold_settings"]
    if saved_settings:
        df = pd.DataFrame.from_dict(saved_settings, orient='index')
        st.dataframe(df)
    else:
        st.write("No saved thresholds yet.")

