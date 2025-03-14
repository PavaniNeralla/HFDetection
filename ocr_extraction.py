import cv2
import pytesseract
import fitz  # PyMuPDF
import numpy as np

# Specify the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocess_image(image):
    """Preprocess the image for better OCR accuracy."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Remove noise
    kernel = np.ones((1, 1), np.uint8)
    processed_image = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return processed_image

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using OCR."""
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    text = ""
    
    for page_num in range(len(pdf_document)):
        # Get the page
        page = pdf_document.load_page(page_num)
        
        # Convert the page to an image
        pix = page.get_pixmap()
        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        
        # Preprocess the image
        processed_image = preprocess_image(image)
        
        # Perform OCR on the preprocessed image
        text += pytesseract.image_to_string(processed_image)
    
    return text