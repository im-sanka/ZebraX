"""
Article Analyzer SubAgent

This subagent is responsible for:
- Analyzing research articles/PDFs
- Answering research questions with TRUE/FALSE classifications
- Creating tabulated results
- Searching for articles if needed
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from .rate_limit import DEFAULT_RETRY_CONFIG
from .instructions.article_analyzer_instruction import ARTICLE_ANALYZER_INSTRUCTION
from .tools.pdf_tools import (
    find_pdf_files,
    list_pdf_files,
    read_pdf_text,
    batch_read_pdfs,
    get_pdf_info,
)
from .tools.table_tools import (
    create_results_table,
    add_result_row,
    update_result_cell,
    get_table_data,
    save_table_to_excel,
    get_table_summary,
)


# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


def create_article_analyzer_agent() -> LlmAgent:
    """
    Creates a subagent that analyzes articles with TRUE/FALSE classifications (Zebra-like).
    
    This subagent:
    - Reads PDFs or searches for articles
    - Answers research questions with TRUE/FALSE
    - Creates tabulated results
    
    Returns:
        LlmAgent: The article analyzer subagent
    """
    article_analyzer = LlmAgent(
        name="article_analyzer",
        model=Gemini(model=GEMINI_MODEL),
        description="Analyzes research articles and answers questions with TRUE/FALSE classifications.",
        instruction=ARTICLE_ANALYZER_INSTRUCTION,
        tools=[
            # PDF tools
            find_pdf_files,
            list_pdf_files,
            read_pdf_text,
            batch_read_pdfs,
            get_pdf_info,
            # Table tools
            create_results_table,
            add_result_row,
            update_result_cell,
            get_table_data,
            save_table_to_excel,
            get_table_summary,
        ],
        output_key="analysis_results_output",
        generate_content_config=DEFAULT_RETRY_CONFIG,
    )
    
    return article_analyzer


# Standalone test
if __name__ == "__main__":
    agent = create_article_analyzer_agent()
    print(f"✅ Created agent: {agent.name}")
    print(f"   Description: {agent.description}")
    print(f"   Tools: {[t.__name__ if hasattr(t, '__name__') else str(t) for t in agent.tools]}")
