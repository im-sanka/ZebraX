"""
PDF Tools for Maestro Agent

Functions for reading, extracting, and analyzing PDF documents.
Reuses functionality from zebra agent but adapted for Maestro workflow.
"""

import fitz  # PyMuPDF
import os
import concurrent.futures
from typing import Dict, List, Any


def find_pdf_files() -> Dict[str, Any]:
    """
    Search for PDF files in common upload directories.
    
    This is useful when files are uploaded via ADK web interface
    and the exact directory is unknown.
    
    Returns:
        Dictionary with found PDF files and their locations.
    """
    # Common directories where uploaded files might be stored
    search_dirs = [
        ".",                    # Current working directory
        "./uploads",            # Common upload folder
        "/tmp",                 # Temp directory
        os.path.expanduser("~"),  # Home directory
        os.getcwd(),            # Explicit current working directory
    ]
    
    found_pdfs = []
    checked_dirs = []
    
    for directory in search_dirs:
        try:
            if os.path.exists(directory) and os.path.isdir(directory):
                checked_dirs.append(directory)
                for filename in os.listdir(directory):
                    if filename.lower().endswith('.pdf'):
                        full_path = os.path.join(directory, filename)
                        # Avoid duplicates
                        if full_path not in [p["path"] for p in found_pdfs]:
                            found_pdfs.append({
                                "filename": filename,
                                "path": os.path.abspath(full_path),
                                "directory": os.path.abspath(directory)
                            })
        except PermissionError:
            continue
        except Exception:
            continue
    
    if found_pdfs:
        # Group by directory
        directories_with_pdfs = list(set(p["directory"] for p in found_pdfs))
        return {
            "success": True,
            "found": True,
            "count": len(found_pdfs),
            "files": found_pdfs,
            "directories_with_pdfs": directories_with_pdfs,
            "message": f"Found {len(found_pdfs)} PDF files in {len(directories_with_pdfs)} location(s).",
            "suggestion": f"Use batch_read_pdfs('{directories_with_pdfs[0]}') to read all PDFs from the first location."
        }
    else:
        return {
            "success": True,
            "found": False,
            "count": 0,
            "files": [],
            "checked_directories": checked_dirs,
            "message": "No PDF files found in common locations. Please provide the directory path where your PDFs are located."
        }


def list_pdf_files(directory: str) -> Dict[str, Any]:
    """
    List all PDF files in a directory.
    
    Args:
        directory: Path to the directory to search.
    
    Returns:
        Dictionary with list of PDF files and count.
    """
    try:
        if not os.path.exists(directory):
            return {"success": False, "error": f"Directory not found: {directory}"}
        
        pdf_files = []
        for filename in os.listdir(directory):
            if filename.lower().endswith('.pdf'):
                pdf_files.append({
                    "filename": filename,
                    "path": os.path.join(directory, filename)
                })
        
        return {
            "success": True,
            "directory": directory,
            "count": len(pdf_files),
            "files": pdf_files
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


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
        
        pages_text = []
        combined_text = ""
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            text = page.get_text()
            pages_text.append({
                "page_number": i + 1,
                "text": text,
                "word_count": len(text.split())
            })
            combined_text += text + "\n"
        
        # Extract title from first page
        title = ""
        if pages_text and pages_text[0]["text"]:
            lines = pages_text[0]["text"].strip().split('\n')
            for line in lines[:5]:  # Check first 5 lines for title
                if len(line.strip()) > 10 and len(line.strip()) < 200:
                    title = line.strip()
                    break
        
        doc.close()
        
        return {
            "success": True,
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "title": title,
            "total_pages": len(pages_text),
            "combined_text": combined_text,
            "total_word_count": len(combined_text.split()),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "file_path": file_path}


def get_pdf_info(file_path: str) -> Dict[str, Any]:
    """
    Get metadata about a PDF file without reading full content.
    
    Args:
        file_path: Path to the PDF file.
    
    Returns:
        Dictionary with PDF metadata.
    """
    try:
        doc = fitz.open(file_path)
        metadata = doc.metadata
        
        info = {
            "success": True,
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "page_count": len(doc),
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
        }
        
        doc.close()
        return info
    except Exception as e:
        return {"success": False, "error": str(e)}


def _read_single_pdf(file_path: str, max_chars: int = None) -> Dict[str, Any]:
    """Helper function to read a single PDF for parallel processing."""
    result = read_pdf_text(file_path)
    if result["success"] and max_chars and len(result.get("combined_text", "")) > max_chars:
        # Truncate to fit context limits
        result["combined_text"] = result["combined_text"][:max_chars]
        result["truncated"] = True
        result["original_char_count"] = result.get("total_word_count", 0) * 5  # estimate
    return result


def batch_read_pdfs(directory: str, max_workers: int = 4, max_chars_per_pdf: int = 50000) -> Dict[str, Any]:
    """
    Read ALL PDFs in a directory in parallel.
    
    This is much more efficient than reading PDFs one by one.
    Each PDF is truncated to max_chars_per_pdf to fit within LLM context limits.
    
    Args:
        directory: Path to the directory containing PDFs.
        max_workers: Maximum number of parallel workers (default: 4).
        max_chars_per_pdf: Maximum characters to extract per PDF (default: 50000, ~12500 tokens).
                          This helps ensure all papers fit within the LLM context window.
    
    Returns:
        Dictionary with all PDF contents and summary.
    """
    try:
        # First, list all PDFs
        pdf_list = list_pdf_files(directory)
        if not pdf_list["success"]:
            return pdf_list
        
        if pdf_list["count"] == 0:
            return {
                "success": True,
                "directory": directory,
                "total_files": 0,
                "papers": [],
                "message": "No PDF files found in directory"
            }
        
        # Read all PDFs in parallel
        file_paths = [f["path"] for f in pdf_list["files"]]
        papers = []
        errors = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(_read_single_pdf, path, max_chars_per_pdf): path 
                for path in file_paths
            }
            
            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    if result["success"]:
                        papers.append(result)
                    else:
                        errors.append({"path": path, "error": result.get("error", "Unknown error")})
                except Exception as e:
                    errors.append({"path": path, "error": str(e)})
        
        # Calculate total characters to help understand context usage
        total_chars = sum(len(p.get("combined_text", "")) for p in papers)
        truncated_count = sum(1 for p in papers if p.get("truncated", False))
        
        return {
            "success": True,
            "directory": directory,
            "total_files": len(file_paths),
            "successful_reads": len(papers),
            "failed_reads": len(errors),
            "truncated_papers": truncated_count,
            "total_characters": total_chars,
            "estimated_tokens": total_chars // 4,  # rough estimate
            "papers": papers,
            "errors": errors if errors else None,
            "note": f"Read {len(papers)} papers. Each paper limited to ~{max_chars_per_pdf} chars to fit LLM context."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
