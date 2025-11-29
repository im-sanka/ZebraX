"""Search Tools for Maestro Agent

Functions for searching and finding research articles online.
Provides helper utilities for article discovery.
"""

from typing import Dict, List, Any, Optional
import re


def search_articles(query: str, num_results: int = 10) -> Dict[str, Any]:
    """
    Search for research articles related to a query using Google.
    
    This function is designed to find academic papers that can help
    answer research questions.
    
    Args:
        query: The search query (research topic or question).
        num_results: Number of results to return (default: 10).
    
    Returns:
        Dictionary with search results containing article information.
    """
    try:
        # Enhance query for academic results
        academic_query = f"{query} research paper PDF OR article"
        
        # Note: In a real implementation, you would call google_search here
        # For now, we return a structured response that the LLM can work with
        
        return {
            "success": True,
            "query": query,
            "enhanced_query": academic_query,
            "num_requested": num_results,
            "message": "Use Google Search tool to find articles with this query",
            "instructions": [
                f"Search for: {academic_query}",
                "Look for PDFs and academic sources",
                "Present results to user for confirmation",
                "Note: User may need to provide their own PDFs for full analysis"
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def download_article_info(url: str) -> Dict[str, Any]:
    """
    Get information about an article from its URL.
    
    Note: This extracts metadata only. Full PDF downloads would require
    user-provided files due to copyright restrictions.
    
    Args:
        url: URL of the article or PDF.
    
    Returns:
        Dictionary with article information.
    """
    try:
        # Extract information from URL
        info = {
            "success": True,
            "url": url,
            "is_pdf": url.lower().endswith('.pdf'),
            "domain": _extract_domain(url),
        }
        
        # Identify source type
        domain = info["domain"].lower()
        if "arxiv" in domain:
            info["source_type"] = "arXiv"
            info["likely_academic"] = True
        elif "ieee" in domain:
            info["source_type"] = "IEEE"
            info["likely_academic"] = True
        elif "acm" in domain:
            info["source_type"] = "ACM Digital Library"
            info["likely_academic"] = True
        elif "springer" in domain:
            info["source_type"] = "Springer"
            info["likely_academic"] = True
        elif "sciencedirect" in domain or "elsevier" in domain:
            info["source_type"] = "ScienceDirect/Elsevier"
            info["likely_academic"] = True
        elif "researchgate" in domain:
            info["source_type"] = "ResearchGate"
            info["likely_academic"] = True
        elif "scholar.google" in domain:
            info["source_type"] = "Google Scholar"
            info["likely_academic"] = True
        else:
            info["source_type"] = "Unknown"
            info["likely_academic"] = False
        
        info["note"] = "For full analysis, please download the PDF and provide the local path."
        
        return info
    except Exception as e:
        return {"success": False, "error": str(e)}


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        # Simple domain extraction
        url = url.replace("https://", "").replace("http://", "")
        domain = url.split("/")[0]
        return domain
    except:
        return ""


def format_search_results_for_display(results: List[Dict[str, str]]) -> str:
    """
    Format search results into a user-friendly display.
    
    Args:
        results: List of search result dictionaries.
    
    Returns:
        Formatted string for display.
    """
    if not results:
        return "No results found."
    
    output = "## Found Articles\n\n"
    
    for i, result in enumerate(results, 1):
        title = result.get("title", "Unknown Title")
        url = result.get("url", "")
        snippet = result.get("snippet", "")
        
        output += f"### {i}. {title}\n"
        output += f"   URL: {url}\n"
        if snippet:
            output += f"   Preview: {snippet[:200]}...\n"
        output += "\n"
    
    output += "\n**Would you like me to proceed with these articles?**"
    output += "\n(Note: For full analysis, you may need to provide downloaded PDFs)"
    
    return output
