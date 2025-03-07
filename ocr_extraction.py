import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
from faiss_db import store_ef_value

def extract_text_from_pdf(pdf_path):
    # Specify the Tesseract executable path
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    """Extracts text from a scanned PDF using OCR."""
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            img = Image.open(io.BytesIO(image_bytes))

            text = pytesseract.image_to_string(img, config="--psm 6")
            full_text += " " + text

    clean_text = " ".join(full_text.split())

    # ✅ Extract EF values using improved regex
    ef_pattern = r"(EF(?:-A2C|-A4C|-Biplane|-PLAX|-PSAX|-Subcostal|-Other)?)[^\d]*(\d{1,2}(?:-\d{1,2})?(?:\.\d+)?)%"
    matches = re.findall(ef_pattern, clean_text)

# ✅ Debug: Print Matched EF Values
    print("\n🔍 Matched EF Values:", matches)

    ef_dict = {match[0]: match[1] + "%" for match in matches}

    # ✅ Store EF values in FAISS for fast retrieval
    if ef_dict:
        store_ef_value(clean_text, ef_dict)

    return ef_dict if ef_dict else "EF value not found."
