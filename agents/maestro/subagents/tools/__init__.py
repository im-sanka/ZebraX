"""
Maestro Tools Package

Contains tools for:
- PDF reading and analysis
- Excel/Table operations
- Result tabulation
"""

from .pdf_tools import (
    read_pdf_text,
    batch_read_pdfs,
    get_pdf_info,
    list_pdf_files,
    find_pdf_files,
)
from .table_tools import (
    create_results_table,
    add_result_row,
    update_result_cell,
    get_table_data,
    save_table_to_excel,
    load_table_from_excel,
    get_table_summary,
    compare_with_reference,
    compare_two_excel_files,
)

__all__ = [
    # PDF tools
    "read_pdf_text",
    "batch_read_pdfs",
    "get_pdf_info",
    "list_pdf_files",
    "find_pdf_files",
    # Table tools
    "create_results_table",
    "add_result_row",
    "update_result_cell",
    "get_table_data",
    "save_table_to_excel",
    "load_table_from_excel",
    "get_table_summary",
    "compare_with_reference",
    "compare_two_excel_files",
]
