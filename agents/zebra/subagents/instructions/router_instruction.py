"""
Router Agent Instruction

Instruction for the router agent that determines request types.
"""

ROUTER_INSTRUCTION = """Analyze the user's request and determine the workflow type(s).

Output ONE OR MORE of these words, comma-separated:
- "classify" - if user wants to classify/analyze papers based on some criterion
- "excel" - if user wants to perform Excel operations (delete column, update cell, get info, etc.)
- "pdf" - if user just wants to read or list PDFs

For COMBINED requests, output multiple types in the order they should execute.

Examples:
- "classify papers based on software" → classify
- "delete the Software column" → excel
- "show me the columns" → excel
- "read the PDFs in test/Articles" → pdf
- "find papers about regression testing" → classify
- "update row 3" → excel
- "classify papers on ML then delete the Year column" → classify,excel
- "read PDFs and update the status column" → pdf,excel
- "classify papers and show me the results" → classify,excel
- "analyze papers for testing coverage and then remove the old Classification column" → classify,excel

Output ONLY the word(s), comma-separated if multiple, nothing else."""
