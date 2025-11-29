"""
Excel Handler SubAgent

This subagent is responsible for:
- Reading existing Excel data
- Adding/deleting columns and rows
- Updating classification results
- Batch updates and transformations
- Matching papers to rows
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from .rate_limit import DEFAULT_RETRY_CONFIG
from .tools.excel_tools import (
    excel_to_json,
    read_excel_data,
    update_excel_row,
    add_column_to_excel,
    get_excel_columns,
    list_pdf_files,
    delete_excel_column,
    delete_excel_row,
    get_cell_value,
    clear_cell,
    get_excel_info,
    batch_update_cells,
    transform_column,
)
from .instructions.excel_handler_instruction import EXCEL_HANDLER_INSTRUCTION


# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


def create_excel_handler_agent() -> LlmAgent:
    """
    Creates a subagent that handles ALL Excel file operations.
    
    This subagent:
    - Reads existing Excel data
    - Creates/deletes columns and rows
    - Updates single cells or batch updates
    - Transforms column values
    - Matches papers to rows by title
    
    Returns:
        LlmAgent: The Excel handler subagent
    """
    excel_handler = LlmAgent(
        name="excel_handler",
        model=Gemini(model=GEMINI_MODEL),
        description="Manages ALL Excel file operations for systematic literature reviews.",
        instruction=EXCEL_HANDLER_INSTRUCTION,
        tools=[
            # Cell operations
            update_excel_row,
            get_cell_value,
            clear_cell,
            # Bulk operations
            batch_update_cells,
            transform_column,
            # Column operations
            add_column_to_excel,
            delete_excel_column,
            get_excel_columns,
            # Row operations
            delete_excel_row,
            # Read operations
            read_excel_data,
            get_excel_info,
            excel_to_json,
            # File operations
            list_pdf_files,
        ],
        output_key="excel_result",
        generate_content_config=DEFAULT_RETRY_CONFIG,
    )
    
    return excel_handler


# Standalone test
if __name__ == "__main__":
    agent = create_excel_handler_agent()
    print(f"✅ Created agent: {agent.name}")
    print(f"   Description: {agent.description}")
    print(f"   Tools: {[t.__name__ for t in agent.tools]}")
