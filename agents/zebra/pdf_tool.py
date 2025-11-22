import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
from typing import Dict, Optional, List, Any

def read_pdf_text(file_path: str, page_range: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    Extract text content from PDF pages.
    
    Args:
        file_path: Path to the PDF file.
        page_range: Optional dict with 'start' and 'end' page numbers (1-based).
    """
    try:
        doc = fitz.open(file_path)
        start_page = 0
        end_page = len(doc)
        
        if page_range:
            start_page = max(0, page_range.get('start', 1) - 1)
            end_page = min(len(doc), page_range.get('end', len(doc)))

        pages_text = []
        combined_text = ""
        
        for i in range(start_page, end_page):
            page = doc.load_page(i)
            text = page.get_text()
            pages_text.append({
                "page_number": i + 1,
                "text": text,
                "word_count": len(text.split())
            })
            combined_text += text + "\n"
            
        return {
            "success": True,
            "file_path": file_path,
            "pages_processed": f"{start_page + 1}-{end_page}",
            "total_pages": len(doc),
            "pages_text": pages_text,
            "combined_text": combined_text,
            "total_word_count": len(combined_text.split()),
            "total_character_count": len(combined_text)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_pdf_images(file_path: str, output_dir: Optional[str] = None, page_range: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    Extract all images from a PDF file.
    
    Args:
        file_path: Path to the PDF file.
        output_dir: Directory to save images. If None, images are not saved to disk but info is returned.
        page_range: Optional dict with 'start' and 'end' page numbers (1-based).
    """
    try:
        doc = fitz.open(file_path)
        start_page = 0
        end_page = len(doc)
        
        if page_range:
            start_page = max(0, page_range.get('start', 1) - 1)
            end_page = min(len(doc), page_range.get('end', len(doc)))
            
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        extracted_images = []
        
        for i in range(start_page, end_page):
            page = doc.load_page(i)
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                image_filename = f"page{i+1}_img{img_index+1}.{image_ext}"
                image_path = ""
                
                if output_dir:
                    image_path = os.path.join(output_dir, image_filename)
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                
                extracted_images.append({
                    "page_number": i + 1,
                    "image_index": img_index + 1,
                    "extension": image_ext,
                    "size": len(image_bytes),
                    "saved_path": image_path
                })
                
        return {
            "success": True,
            "file_path": file_path,
            "images_extracted": len(extracted_images),
            "images": extracted_images
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def read_pdf_with_ocr(file_path: str, page_range: Optional[Dict[str, int]] = None, ocr_language: str = "eng") -> Dict[str, Any]:
    """
    Extract text from both regular text and images using OCR.
    
    Args:
        file_path: Path to the PDF file.
        page_range: Optional dict with 'start' and 'end' page numbers (1-based).
        ocr_language: OCR language code (default: "eng").
    """
    try:
        doc = fitz.open(file_path)
        start_page = 0
        end_page = len(doc)
        
        if page_range:
            start_page = max(0, page_range.get('start', 1) - 1)
            end_page = min(len(doc), page_range.get('end', len(doc)))
            
        pages_data = []
        all_text_combined = ""
        
        for i in range(start_page, end_page):
            page = doc.load_page(i)
            text = page.get_text()
            
            # OCR on images
            image_list = page.get_images(full=True)
            images_ocr_text = []
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                image = Image.open(io.BytesIO(image_bytes))
                ocr_text = pytesseract.image_to_string(image, lang=ocr_language)
                
                images_ocr_text.append({
                    "image_index": img_index + 1,
                    "ocr_text": ocr_text.strip(),
                    "confidence": "unknown" # Tesseract can provide confidence but keeping it simple
                })
            
            combined_page_text = text + "\n" + "\n".join([img['ocr_text'] for img in images_ocr_text])
            
            pages_data.append({
                "page_number": i + 1,
                "text": text,
                "ocr_text": "\n".join([img['ocr_text'] for img in images_ocr_text]),
                "images_with_text": images_ocr_text,
                "combined_text": combined_page_text,
                "text_word_count": len(text.split()),
                "ocr_word_count": sum(len(img['ocr_text'].split()) for img in images_ocr_text)
            })
            
            all_text_combined += combined_page_text + "\n"
            
        return {
            "success": True,
            "file_path": file_path,
            "pages_processed": f"{start_page + 1}-{end_page}",
            "ocr_language": ocr_language,
            "pages_data": pages_data,
            "all_text_combined": all_text_combined
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_pdf_info(file_path: str) -> Dict[str, Any]:
    """
    Get comprehensive metadata and statistics about a PDF.
    """
    try:
        doc = fitz.open(file_path)
        metadata = doc.metadata
        return {
            "success": True,
            "file_path": file_path,
            "page_count": len(doc),
            "metadata": metadata,
            "is_encrypted": doc.is_encrypted
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def analyze_pdf_structure(file_path: str) -> Dict[str, Any]:
    """
    Analyze the structure and content distribution of a PDF.
    """
    try:
        doc = fitz.open(file_path)
        toc = doc.get_toc()
        return {
            "success": True,
            "file_path": file_path,
            "toc": toc,
            "page_count": len(doc)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
