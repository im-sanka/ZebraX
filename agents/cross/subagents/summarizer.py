"""
Cross Summarizer SubAgent

This subagent is responsible for:
- Providing final response to user after comparison operations complete
- Summarizing statistical results
- Interpreting Cohen's Kappa and agreement rates
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from .rate_limit import DEFAULT_RETRY_CONFIG
from .instructions.cross_summarizer_instruction import CROSS_SUMMARIZER_INSTRUCTION


# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


def create_cross_summarizer_agent() -> LlmAgent:
    """
    Creates a subagent that provides final summary of comparison results.
    
    This subagent:
    - Reads comparison results from session state
    - Provides clear statistical summaries
    - Interprets metrics in plain language
    
    Returns:
        LlmAgent: The summarizer subagent
    """
    summarizer = LlmAgent(
        name="cross_summarizer",
        model=Gemini(model=GEMINI_MODEL),
        description="Provides final summary of cross-comparison results.",
        instruction=CROSS_SUMMARIZER_INSTRUCTION,
        output_key="final_response",
        generate_content_config=DEFAULT_RETRY_CONFIG,
    )
    
    return summarizer
