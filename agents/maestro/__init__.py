"""
Maestro Agent Package

A sequential orchestrator agent that combines:
1. Research question formulation (like Belo)
2. Article analysis with TRUE/FALSE classification (like Zebra)
3. Cross-validation and summarization (like Cross)
"""

from .agent import create_maestro_agent, root_agent

__all__ = ["create_maestro_agent", "root_agent"]
