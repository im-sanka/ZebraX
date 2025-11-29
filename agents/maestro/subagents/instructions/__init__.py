"""
Maestro Subagent Instructions Package

Contains instruction constants for all Maestro subagents.
"""

from .research_advisor_instruction import RESEARCH_ADVISOR_INSTRUCTION
from .article_analyzer_instruction import ARTICLE_ANALYZER_INSTRUCTION
from .validator_instruction import VALIDATOR_INSTRUCTION
from .maestro_router_instruction import MAESTRO_ROUTER_INSTRUCTION

__all__ = [
    "RESEARCH_ADVISOR_INSTRUCTION",
    "ARTICLE_ANALYZER_INSTRUCTION",
    "VALIDATOR_INSTRUCTION",
    "MAESTRO_ROUTER_INSTRUCTION",
]
