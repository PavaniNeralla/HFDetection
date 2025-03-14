import streamlit as st
from gemini_analysis import analyze_with_gemini, parse_gemini_response
from ocr_extraction import extract_text_from_pdf
from risk_analysis import determine_risk

def process_uploaded_file(uploaded_file, threshold_settings):
    try:
        pdf_path = f"temp_files/{uploaded_file.name}"
        
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        extracted_text = extract_text_from_pdf(pdf_path)
        extracted_text = str(extracted_text) if extracted_text else ""

        if not extracted_text.strip():
            return {"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "No EF Value Found"}

        ai_analysis = analyze_with_gemini(extracted_text, threshold_settings)

        if not isinstance(ai_analysis, dict) or "error" in ai_analysis:
            return {"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "Error: Gemini failed"}

        extracted_values = parse_gemini_response(ai_analysis)

        if not isinstance(extracted_values, dict):
            return {"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": "Error processing EF values"}

        valid_values = {}
        risk_values = {}

        for metric, value in extracted_values.items():
            try:
                value_cleaned = str(value).replace("%", "").strip('"').strip()

                if "-" in value_cleaned:
                    lower_bound = float(value_cleaned.split("-")[0])
                else:
                    lower_bound = float(value_cleaned)

                valid_values[metric] = value_cleaned
                risk_values[metric] = lower_bound
            except ValueError:
                continue  
            except Exception:
                continue  

        risk_nature = determine_risk(risk_values, threshold_settings) if risk_values else "NA"
        values_combined = "; ".join([f"{key}: {value}" for key, value in valid_values.items()]) if valid_values else "NA"

        return {
            "Report Name": uploaded_file.name.replace(".pdf", ""),
            "Risk Nature": risk_nature,
            "EF Values": values_combined
        }

    except Exception as e:
        return {"Report Name": uploaded_file.name.replace(".pdf", ""), "Risk Nature": "NA", "EF Values": f"Error: {e}"}
