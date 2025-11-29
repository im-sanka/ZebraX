"""
PDF Tools for Zebra Agent

Functions for reading, extracting, and analyzing PDF documents.
Includes batch processing for efficient parallel operations.
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
import concurrent.futures
from typing import Dict, Optional, List, Any


def read_pdf_text(file_path: str) -> Dict[str, Any]:
    """
    Extract text content from all PDF pages.
    
    Args:
        file_path: Path to the PDF file.
    
    Returns:
        Dictionary with extracted text and metadata.
    """
    try:
        doc = fitz.open(file_path)
        start_page = 0
        end_page = len(doc)

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


def extract_pdf_images(file_path: str) -> Dict[str, Any]:
    """
    Extract all images from a PDF file.
    
    Args:
        file_path: Path to the PDF file.
    
    Returns:
        Dictionary with extracted image information.
    """
    try:
        doc = fitz.open(file_path)
        start_page = 0
        end_page = len(doc)
        output_dir = None
            
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


def read_pdf_with_ocr(file_path: str, ocr_language: str = "eng") -> Dict[str, Any]:
    """
    Extract text from both regular text and images using OCR.
    
    Args:
        file_path: Path to the PDF file.
        ocr_language: OCR language code (default: "eng").
    
    Returns:
        Dictionary with extracted text including OCR results.
    """
    try:
        doc = fitz.open(file_path)
        start_page = 0
        end_page = len(doc)
            
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
                    "confidence": "unknown"
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
    
    Args:
        file_path: Path to the PDF file.
    
    Returns:
        Dictionary with PDF metadata.
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
    
    Args:
        file_path: Path to the PDF file.
    
    Returns:
        Dictionary with PDF structure information.
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


def _read_single_pdf(file_path: str) -> Dict[str, Any]:
    """
    Internal function to read a single PDF. Used by batch_read_pdfs.
    Returns a simplified result with just the essential info.
    """
    try:
        doc = fitz.open(file_path)
        combined_text = ""
        for page in doc:
            combined_text += page.get_text() + "\n"
        
        filename = os.path.basename(file_path)
        return {
            "file_path": file_path,
            "filename": filename,
            "success": True,
            "text": combined_text,
            "page_count": len(doc),
            "word_count": len(combined_text.split())
        }
    except Exception as e:
        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "success": False,
            "error": str(e)
        }


def batch_read_pdfs(directory: str, max_workers: int = 5) -> Dict[str, Any]:
    """
    Read multiple PDF files in parallel for faster processing.
    
    This function reads all PDFs in a directory concurrently using thread pooling,
    significantly reducing total processing time compared to sequential reading.
    
    Args:
        directory: Path to the directory containing PDF files.
        max_workers: Maximum number of concurrent readers (default: 5).
                    Higher values = faster but more memory usage.
    
    Returns:
        Dictionary with:
        - papers: List of paper data with filename, text, and metadata
        - total_count: Number of PDFs processed
        - success_count: Number successfully read
        - failed_count: Number that failed to read
        - errors: List of any errors encountered
    
    Example:
        >>> result = batch_read_pdfs("data/01/", max_workers=5)
        >>> for paper in result["papers"]:
        ...     print(f"{paper['filename']}: {paper['word_count']} words")
    """
    try:
        if not os.path.exists(directory):
            return {"success": False, "error": f"Directory not found: {directory}"}
        
        # Get all PDF files
        pdf_files = []
        for filename in os.listdir(directory):
            if filename.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(directory, filename))
        
        if not pdf_files:
            return {
                "success": True,
                "papers": [],
                "total_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "message": "No PDF files found in directory"
            }
        
        # Process PDFs in parallel
        papers = []
        errors = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(_read_single_pdf, pdf_file): pdf_file 
                for pdf_file in pdf_files
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                result = future.result()
                if result["success"]:
                    papers.append(result)
                else:
                    errors.append(result)
        
        # Sort by filename for consistent ordering
        papers.sort(key=lambda x: x["filename"])
        
        return {
            "success": True,
            "papers": papers,
            "total_count": len(pdf_files),
            "success_count": len(papers),
            "failed_count": len(errors),
            "errors": errors if errors else None,
            "message": f"Read {len(papers)} PDFs in parallel (max {max_workers} workers)"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
