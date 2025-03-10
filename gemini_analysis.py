import google.generativeai as genai
import os
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

def analyze_with_gemini(text):
    """Analyzes text using Gemini Pro."""
    prompt = (
        "Extract all Ejection Fraction (EF) values from this medical report, including LVEF, EF-A2C, "
        "EF-A4C, EF-Biplane, EF-PLAX, EF-PSAX, EF-Subcostal, EF-Other, EF-Global, and EF-Mmode. "
        "Provide the EF values in the format:\n"
        "EF Type: Value (or Value-Range if applicable).\n"
        "If an EF value is not found, mention 'No EF found'.\n\n"
        "Report:\n"
        f"{text}"
    )

    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt)

        if response:
            print("Gemini API Response:", response.text.strip())  # Debugging information
            return response.text.strip()
        else:
            return "Error: No response from Gemini API"

    except ResourceExhausted:
        return "Error: Gemini API quota exhausted. Please try again later."