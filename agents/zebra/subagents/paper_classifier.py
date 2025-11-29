"""
Paper Classifier SubAgent

This subagent is responsible for:
- Reading PDF documents
- Classifying research papers based on specified criteria
- Providing evidence-based classifications
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from .rate_limit import DEFAULT_RETRY_CONFIG
from .tools.pdf_tools import batch_read_pdfs, read_pdf_text, get_pdf_info
from .tools.excel_tools import list_pdf_files
from .instructions.paper_classifier_instruction import PAPER_CLASSIFIER_INSTRUCTION


# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


def create_paper_classifier_agent() -> LlmAgent:
    """
    Creates a subagent that reads and classifies research papers.
    
    This subagent:
    - Reads PDFs using batch processing
    - Classifies papers based on user-specified criteria
    - Provides evidence for each classification
    
    Returns:
        LlmAgent: The paper classifier subagent
    """
    paper_classifier = LlmAgent(
        name="paper_classifier",
        model=Gemini(model=GEMINI_MODEL),
        description="Reads and classifies research papers based on specified criteria.",
        instruction=PAPER_CLASSIFIER_INSTRUCTION,
        tools=[
            list_pdf_files,
            batch_read_pdfs,
            read_pdf_text,
            get_pdf_info,
        ],
        output_key="classification_result",
        generate_content_config=DEFAULT_RETRY_CONFIG,
    )
    
    return paper_classifier
