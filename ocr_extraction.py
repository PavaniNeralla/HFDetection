import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF. Falls back to OCR if direct extraction fails."""
    try:
        # Try to extract text directly from the PDF
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        # If text is found, return it
        if full_text.strip():
            return " ".join(full_text.split())
        
        # If no text is found, fall back to OCR
        raise ValueError("No text found, falling back to OCR")

    except Exception as e:
        print(f"Direct text extraction failed: {e}. Falling back to OCR.")
        # Fall back to OCR
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                base_image = doc.extract_image(xref)
                img = Image.open(io.BytesIO(base_image["image"]))
                text = pytesseract.image_to_string(img, config="--psm 6")
                full_text += " " + text

        return " ".join(full_text.split())