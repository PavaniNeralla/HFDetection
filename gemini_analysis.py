import google.generativeai as genai
import os
import pandas as pd
import io
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted

# Load API key
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

def extract_text_from_response(response):
    """Extracts text correctly from Gemini API structured response."""
    try:
        if response and hasattr(response, "candidates") and response.candidates:
            text_response = response.candidates[0].content.parts[0].text
            if isinstance(text_response, str):
                return text_response.strip()
            else:
                print("Unexpected text type:", type(text_response))
                return ""
        else:
            print("Unexpected response format:", response)
            return ""  # Return an empty string instead of None or dict
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        return ""

def analyze_with_gemini(text, threshold_settings):
    """Extracts EF and additional metrics using Gemini, ensuring CSV response format."""

    predefined_metrics = ["LVEF", "LVEF-Mmode", "EF-A2C", "EF-A4C", "EF-Biplane",
                          "EF-PLAX", "EF-PSAX", "EF-Subcostal", "EF-Other", "EF-Global", "EF-Mmode"]
    
    additional_metrics = list(threshold_settings.keys()) if threshold_settings else []
    metrics = predefined_metrics + additional_metrics

    metric_lines = "\n".join([f"{metric},value or 'No {metric} found'" for metric in metrics])

    prompt = f"""
    You are a medical AI assistant. Extract the following values from the given medical report.

    **Return ONLY CSV format. No extra text. No code blocks.**  

    **CSV format:**
    Metric,Value
    {metric_lines}

    Report:
    ```
    {text}
    ```
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        gemini_response = model.generate_content(prompt)

        # Extract actual text response
        csv_text = extract_text_from_response(gemini_response)

        if not isinstance(csv_text, str):
            print("Unexpected response type:", type(csv_text))
            return {"error": "Invalid response format from Gemini API"}
        
        csv_text = csv_text.strip()
        if not csv_text:
            return {"error": "Empty response from Gemini API"}

        # Debugging Output
        print("Extracted Gemini Response:\n", csv_text)

        # Convert CSV response to dictionary
        try:
            df = pd.read_csv(io.StringIO(csv_text))
            if "Metric" not in df.columns or "Value" not in df.columns:
                raise ValueError("CSV does not contain expected 'Metric' and 'Value' columns.")
            
            extracted_values = dict(zip(df["Metric"], df["Value"]))
            return extracted_values
        except Exception as e:
            print("ERROR parsing CSV:", str(e))
            return {"error": f"Failed to process CSV response: {str(e)}"}

    except ResourceExhausted:
        return {"error": "Gemini API quota exhausted. Please try again later."}

def parse_gemini_response(ai_analysis):
    if not isinstance(ai_analysis, dict):
        print("🚨 Gemini response is not a dictionary:", ai_analysis)
        return {}  # Return an empty dictionary in case of failure
    return ai_analysis  # Return it as is
