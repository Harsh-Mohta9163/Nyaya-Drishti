import logging
import pymupdf4llm
from pathlib import Path

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Layout-aware PDF → clean Markdown using PyMuPDF4LLM.
    This replaces the legacy Tesseract/PyMuPDF hybrid approach.
    """
    try:
        logger.info(f"Extracting text from {pdf_path} using PyMuPDF4LLM")
        
        # Check if file exists
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")
            
        md_text = pymupdf4llm.to_markdown(pdf_path)
        
        if not md_text or not md_text.strip():
            logger.warning("PyMuPDF4LLM returned empty text, falling back to legacy extraction")
            return _legacy_extract(pdf_path)
            
        return md_text
        
    except Exception as e:
        logger.error(f"Error in PyMuPDF4LLM extraction: {str(e)}")
        logger.info("Falling back to legacy extraction")
        return _legacy_extract(pdf_path)

def _legacy_extract(pdf_path: str) -> str:
    """Fallback extraction method in case PyMuPDF4LLM fails."""
    import fitz
    
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Legacy extraction failed: {str(e)}")
        return ""