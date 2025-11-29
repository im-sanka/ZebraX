"""
Research Advisor SubAgent

This subagent is responsible for:
- Helping users formulate research questions
- Suggesting focused, researchable questions
- Understanding user's research interests
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from .rate_limit import DEFAULT_RETRY_CONFIG
from .instructions.research_advisor_instruction import RESEARCH_ADVISOR_INSTRUCTION


# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


def create_research_advisor_agent() -> LlmAgent:
    """
    Creates a subagent that helps formulate research questions (Belo-like).
    
    This subagent:
    - Understands user's research interests
    - Formulates clear, researchable questions
    - Provides questions suitable for TRUE/FALSE classification
    
    Returns:
        LlmAgent: The research advisor subagent
    """
    research_advisor = LlmAgent(
        name="research_advisor",
        model=Gemini(model=GEMINI_MODEL),
        description="A PhD-level research advisor that helps formulate research questions.",
        instruction=RESEARCH_ADVISOR_INSTRUCTION,
        output_key="research_questions_output",
        generate_content_config=DEFAULT_RETRY_CONFIG,
    )
    
    return research_advisor


# Standalone test
if __name__ == "__main__":
    agent = create_research_advisor_agent()
    print(f"✅ Created agent: {agent.name}")
    print(f"   Description: {agent.description}")
