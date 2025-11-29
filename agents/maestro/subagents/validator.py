"""
Validator SubAgent

This subagent is responsible for:
- Cross-validating analysis results with reference tables
- Calculating agreement metrics (Cohen's Kappa)
- Providing comprehensive summaries
- Identifying discrepancies
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from .rate_limit import DEFAULT_RETRY_CONFIG
from .instructions.validator_instruction import VALIDATOR_INSTRUCTION
from .tools.table_tools import (
    load_table_from_excel,
    get_table_data,
    get_table_summary,
    compare_with_reference,
    compare_two_excel_files,
)


# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


def create_validator_agent() -> LlmAgent:
    """
    Creates a subagent that validates and summarizes results (Cross-like).
    
    This subagent:
    - Compares results with reference tables
    - Calculates Cohen's Kappa and agreement rates
    - Provides comprehensive summaries
    
    Returns:
        LlmAgent: The validator subagent
    """
    validator = LlmAgent(
        name="validator",
        model=Gemini(model=GEMINI_MODEL),
        description="Validates analysis results and provides summaries with statistical metrics.",
        instruction=VALIDATOR_INSTRUCTION,
        tools=[
            load_table_from_excel,
            get_table_data,
            get_table_summary,
            compare_with_reference,
            compare_two_excel_files,
        ],
        output_key="validation_output",
        generate_content_config=DEFAULT_RETRY_CONFIG,
    )
    
    return validator


# Standalone test
if __name__ == "__main__":
    agent = create_validator_agent()
    print(f"✅ Created agent: {agent.name}")
    print(f"   Description: {agent.description}")
    print(f"   Tools: {[t.__name__ for t in agent.tools]}")
