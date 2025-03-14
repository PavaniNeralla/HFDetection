import re
import json
import os

# Load threshold settings from JSON file
THRESHOLD_FILE = "threshold_settings.json"

def load_threshold_settings():
    """Load metric threshold settings from a JSON file."""
    if os.path.exists(THRESHOLD_FILE):
        with open(THRESHOLD_FILE, "r") as file:
            return json.load(file)
    return {}

# Ensure correct extraction of EF values
def extract_values(ai_output):
    extracted_values = {}
    
    # Split lines and parse CSV format
    lines = ai_output.strip().split("\n")[1:]  # Skip header row
    
    for line in lines:
        try:
            metric, value = line.split(",", 1)  # Ensure only first comma is split
            metric = metric.strip()
            value = value.strip()

            # Normalize values: Convert "No EF-PLAX found" to "NA"
            if "No" in value:
                value = "NA"

            extracted_values[metric] = value
        except ValueError:
            continue  # Skip malformed lines

    return extracted_values


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
    