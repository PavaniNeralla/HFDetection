import google.generativeai as genai
import os
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

def analyze_with_gemini(text):
    """Analyzes text using Gemini Pro with a structured response format."""
    prompt = (
        "Extract all Ejection Fraction (EF) values from this medical report. "
        "Follow these rules:\n"
        "1. If there is no Date of Service, extract all EF values.\n"
        "2. If multiple Dates of Service are present, extract only the EF value from the latest Date of Service.\n\n"
        "Provide the EF values in the exact format:\n\n"
        "LVEF: [Value or Range]\n"
        "LVEF-Mmode: [Value or Range]\n"
        "EF-A2C: [Value or Range]\n"
        "EF-A4C: [Value or Range]\n"
        "EF-Biplane: [Value or Range]\n"
        "EF-PLAX: [Value or 'No EF found']\n"
        "EF-PSAX: [Value or 'No EF found']\n"
        "EF-Subcostal: [Value or 'No EF found']\n"
        "EF-Other: [Value or 'No EF found']\n"
        "EF-Global: [Value or 'No EF found']\n"
        "EF-Mmode: [Value or Range]\n\n"
        "If a value is missing, respond with 'No EF found' in place of the value.\n"
        "Ensure accuracy by selecting only the latest EF values when multiple Dates of Service are present.\n\n"
        "Report:\n"
        f"{text}"
    )

    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt)

        if response and response.text:
            print("Gemini API Response:", response.text.strip())  # Debugging information
            return response.text.strip()
        else:
            return "Error: No response from Gemini API"

    except ResourceExhausted:
        return "Error: Gemini API quota exhausted. Please try again later."
