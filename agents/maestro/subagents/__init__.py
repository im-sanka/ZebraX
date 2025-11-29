"""
Maestro Subagents Package

Contains the specialized subagents:
- research_advisor: Formulates research questions (Belo-like)
- article_analyzer: Analyzes articles with TRUE/FALSE (Zebra-like)
- validator: Cross-validates and summarizes results (Cross-like)
"""

from .research_advisor import create_research_advisor_agent
from .article_analyzer import create_article_analyzer_agent
from .validator import create_validator_agent
from .rate_limit import DEFAULT_RETRY_CONFIG

__all__ = [
    "create_research_advisor_agent",
    "create_article_analyzer_agent",
    "create_validator_agent",
    "DEFAULT_RETRY_CONFIG",
]
