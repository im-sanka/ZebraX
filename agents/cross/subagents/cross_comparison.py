"""
Cross Comparison SubAgent

This subagent is responsible for:
- Comparing two Excel tables
- Calculating statistical metrics (agreement rate, Cohen's Kappa)
- Identifying disagreements between tables
- Providing detailed comparison reports
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from .rate_limit import DEFAULT_RETRY_CONFIG
from .instructions.cross_comparison_instruction import CROSS_COMPARISON_INSTRUCTION
from .tools.cross_tools import (
    load_table,
    get_table_info,
    compare_tables_overview,
    compare_column_values,
    compare_multiple_columns,
    calculate_cohens_kappa,
    calculate_all_agreement_metrics,
    get_disagreement_report,
    full_statistical_comparison,
)


# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


def create_cross_comparison_agent() -> LlmAgent:
    """
    Creates a subagent that compares two Excel tables.
    
    This subagent:
    - Compares table structures and columns
    - Calculates agreement rates and Cohen's Kappa
    - Identifies and reports disagreements
    - Provides comprehensive statistical analysis
    
    Returns:
        LlmAgent: The cross comparison subagent
    """
    cross_comparison = LlmAgent(
        name="cross_comparison",
        model=Gemini(model=GEMINI_MODEL),
        description="Compares two Excel tables and provides statistical analysis.",
        instruction=CROSS_COMPARISON_INSTRUCTION,
        tools=[
            load_table,
            get_table_info,
            compare_tables_overview,
            compare_column_values,
            compare_multiple_columns,
            calculate_cohens_kappa,
            calculate_all_agreement_metrics,
            get_disagreement_report,
            full_statistical_comparison,
        ],
        output_key="comparison_result",
        generate_content_config=DEFAULT_RETRY_CONFIG,
    )
    
    return cross_comparison
