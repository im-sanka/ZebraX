"""
Summarizer SubAgent

This subagent is responsible for:
- Providing final response to user after operations complete
- Summarizing what was accomplished
- Reporting results from classification and Excel operations
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from .rate_limit import DEFAULT_RETRY_CONFIG
from .instructions.zebra_summarizer_instruction import ZEBRA_SUMMARIZER_INSTRUCTION


# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


def create_summarizer_agent() -> LlmAgent:
    """
    Creates a subagent that provides final response to user.
    
    This subagent:
    - Reads results from session state (excel_result, classification_result)
    - Summarizes what was accomplished
    - Provides friendly confirmation message
    
    Returns:
        LlmAgent: The summarizer subagent
    """
    summarizer = LlmAgent(
        name="summarizer",
        model=Gemini(model=GEMINI_MODEL),
        description="Provides final summary response to user after operations complete.",
        instruction=ZEBRA_SUMMARIZER_INSTRUCTION,
        output_key="final_response",
        generate_content_config=DEFAULT_RETRY_CONFIG,
    )
    
    return summarizer
