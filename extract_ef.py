import re

def extract_ef_values(text):
    """Extracts EF values from text, replacing missing values with 'NA'. If all are missing, return overall 'NA'."""
    ef_keys = ["LVEF", "EF-A2C", "EF-A4C", "EF-Biplane", "EF-PLAX", "EF-PSAX", 
               "EF-Subcostal", "EF-Other", "EF-Global", "EF-Mmode"]
    ef_values = {key: "NA" for key in ef_keys}  # Default all EF values to "NA"

    found_any_value = False  # Flag to track if any EF value is found

    for line in text.split("\n"):
        match = re.match(r"(LVEF|EF-[A-Za-z0-9]+):\s*([\d.]+(?:\s*to\s*[\d.]+)?|\bNo EF found\b)", line, re.IGNORECASE)
        if match:
            key, value = match.groups()
            if value and "No EF found" not in value:
                ef_values[key] = value.strip()
                found_any_value = True  # At least one EF value found

    # If no valid EF values were found, return all "NA" and mark risk as "NA"
    if not found_any_value:
        return {key: "NA" for key in ef_keys}, "NA"

    return ef_values, None  # None means risk should be determined


def determine_risk(ef_values):
    """Determines risk based on EF values. High Risk if any EF < 40%. Returns NA if all EF values are missing."""
    if all(value == "NA" for value in ef_values.values()):
        return "NA"

    for value in ef_values.values():
        match = re.search(r"(\d+)(?:\s*to\s*(\d+))?", value)  # Matches single or range values
        if match:
            lower_bound = float(match.group(1))
            if lower_bound < 40.0:
                return "High Risk"

    return "Low Risk"
