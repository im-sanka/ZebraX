"""
Cross Agent Instruction (Router)

Instruction for the router that determines what type of comparison to perform.
"""

CROSS_ROUTER_INSTRUCTION = """Analyze the user's request and determine the comparison type.

Output ONE of these words:
- "compare" - if user wants to compare tables, columns, or get statistics
- "info" - if user just wants information about a table (columns, rows)

Examples:
- "compare the Software column between two tables" → compare
- "what columns are in table1.xlsx" → info
- "calculate Cohen's Kappa for Regression" → compare
- "show me the disagreements" → compare
- "how many rows in the first table" → info
- "give me statistics for Testing column" → compare
- "full comparison of both tables" → compare

Output ONLY the word, nothing else."""
