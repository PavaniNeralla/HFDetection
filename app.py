import streamlit as st
import os
import json
import pandas as pd
from ocr_extraction import extract_text_from_pdf
from gemini_analysis import analyze_with_gemini, parse_gemini_response

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
            try:
                pdf_path = os.path.join("temp_files", uploaded_file.name)
                
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                extracted_text = extract_text_from_pdf(pdf_path)

                # ✅ Ensure extracted_text is always a string
                extracted_text = str(extracted_text) if extracted_text else ""

                if not extracted_text.strip():
                    st.warning(f"⚠️ No text extracted from {uploaded_file.name}. Skipping.")
                    results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "No EF Value Found"})
                    continue

                # Load thresholds
                threshold_settings = st.session_state["threshold_settings"]

                # Get AI analysis with dynamic prompt
                ai_analysis = analyze_with_gemini(extracted_text, threshold_settings)

                # ✅ Ensure ai_analysis is a dictionary
                if not isinstance(ai_analysis, dict):
                    st.error(f"🚨 Error: Unexpected response format from Gemini for {uploaded_file.name}")
                    results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "Error: Gemini failed"})
                    continue

                if "error" in ai_analysis:
                    st.error(f"🚨 Error from Gemini API for {uploaded_file.name}: {ai_analysis['error']}")
                    results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "Error: Gemini failed"})
                    continue
                
                extracted_values = parse_gemini_response(ai_analysis)

                # ✅ Ensure extracted_values is a dictionary before iterating
                if not isinstance(extracted_values, dict):
                    st.error(f"🚨 Error processing EF values for {uploaded_file.name}")
                    results.append({"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "Error processing EF values"})
                    continue

                valid_values = {}
                risk_values = {}

                for metric, value in extracted_values.items():
                    try:
                        # ✅ Ensure value is a string
                        value = str(value)

                        # ✅ Handle missing or invalid values
                        if "no" in value.lower():
                            continue

                        # ✅ Clean percentage and unwanted characters
                        value_cleaned = value.replace("%", "").strip('"').strip()

                        # ✅ Convert only valid numeric values
                        if "-" in value_cleaned:
                            lower_bound = float(value_cleaned.split("-")[0])
                            value_num = value_cleaned
                        else:
                            lower_bound = value_num = float(value_cleaned)

                        valid_values[metric] = value_num  # Store extracted values
                        risk_values[metric] = lower_bound  # Store numeric values for risk

                    except ValueError:
                        continue  
                    except Exception:
                        continue  

                # ✅ Determine Risk Dynamically
                def determine_risk(risk_values, threshold_settings):
                    for metric, value in risk_values.items():
                        threshold = threshold_settings.get(metric, {})
                        condition = threshold.get("condition", "less than")
                        limit1 = threshold.get("value", 40)
                        limit2 = threshold.get("value2", None)

                        # ✅ Ensure EF values below the threshold are correctly classified as High Risk
                        if "EF" in metric and value < 40:  
                            return "High Risk"
                        
                        if condition == "less than" and value < limit1:
                            return "High Risk"
                        elif condition == "greater than" and value > limit1:
                            return "High Risk"
                        elif condition == "between" and limit2 is not None:
                            if not (limit1 <= value <= limit2):
                                return "High Risk"
                    return "Low Risk"


                risk_nature = determine_risk(risk_values, threshold_settings) if risk_values else "NA"
                values_combined = "; ".join([f"{key}: {value}" for key, value in valid_values.items()]) if valid_values else "NA"

                results.append({
                    "Report Name": uploaded_file.name.replace(".pdf", ""),
                    "Risk Nature": risk_nature,
                    "EF Values": values_combined
                })

            except Exception as e:
                st.error(f"❌ Error processing file {uploaded_file.name}: {e}")

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
