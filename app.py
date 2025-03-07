import streamlit as st
import os
from ocr_extraction import extract_text_from_pdf
from gemini_analysis import analyze_with_rag

# ✅ Streamlit UI
st.set_page_config(page_title="EF Value Extractor", layout="centered")
st.title("HF Detection")

uploaded_file = st.file_uploader("📂 Upload a Scanned PDF", type="pdf")

if uploaded_file:
    st.info("Processing the uploaded PDF... Please wait.")

    # ✅ Save uploaded file temporarily
    pdf_path = os.path.join("temp_files", uploaded_file.name)
    os.makedirs("temp_files", exist_ok=True)

    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # ✅ Extract EF values
    with st.spinner("🔄 Extracting EF values from PDF..."):
        ef_values = extract_text_from_pdf(pdf_path)

    if "EF value not found" in ef_values:
        st.error("❌ No EF value found.")
    else:
        st.success(f"✅ Extracted EF Values: {ef_values}")

        # ✅ Retrieve EF values using FAISS (if available)
        with st.spinner("🔄 Retrieving EF values using FAISS..."):
            ef_value = analyze_with_rag(" ".join(ef_values))
            st.success(f"✅ Final EF Value: {ef_value}")
