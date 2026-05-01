"""
PDF text extraction with OCR fallback.

Digital-born PDFs → PyMuPDF direct extraction.
Scanned PDFs (no text layer) → Tesseract OCR.
Hybrid PDFs → per-page routing.
"""
from pathlib import Path


def _has_text_layer(page) -> bool:
    """Check if a PDF page has a meaningful text layer."""
    text = page.get_text("text").strip()
    return len(text) > 50  # Threshold: at least 50 chars


def _ocr_page(page) -> str:
    """OCR a single page using Tesseract via PIL."""
    try:
        import pytesseract
        from PIL import Image
        import io

        # Render page to image at 300 DPI for good OCR quality
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang="eng")
        return text
    except Exception as e:
        return f"[OCR failed: {e}]"


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.

    Returns tuple-like string with embedded metadata about extraction quality.
    Routes each page through digital extraction or OCR based on text layer presence.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return Path(pdf_path).stem.replace("_", " ")

    try:
        document = fitz.open(pdf_path)
    except Exception as e:
        return f"[PDF open failed: {e}]"

    text_chunks = []
    ocr_pages = 0
    total_pages = len(document)

    for page_num, page in enumerate(document):
        if _has_text_layer(page):
            # Digital-born: direct text extraction
            page_text = page.get_text("text")
        else:
            # Scanned: OCR fallback
            page_text = _ocr_page(page)
            ocr_pages += 1

        if page_text.strip():
            text_chunks.append(f"--- Page {page_num + 1} ---\n{page_text}")

    document.close()

    full_text = "\n".join(text_chunks)

    # Append extraction metadata
    if ocr_pages > 0:
        full_text += f"\n\n[Extraction: {total_pages} pages, {ocr_pages} via OCR, {total_pages - ocr_pages} digital]"

    return full_text