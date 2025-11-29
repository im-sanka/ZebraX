"""
Maestro Agent - Sequential Orchestrator for Literature Review

This is the main orchestrator agent that combines three approaches:
1. Research Question Formulation (Belo-like) - Helps users create research questions
2. Article Analysis (Zebra-like) - Analyzes articles with TRUE/FALSE classifications
3. Validation & Summary (Cross-like) - Validates results and provides summaries

Uses Google ADK's BaseAgent pattern with _run_async_impl for custom sequential orchestration.
The workflow is interactive and waits for user input at each stage.
"""

import os
import sys
import asyncio
import logging
from typing import AsyncGenerator
from typing_extensions import override
from dotenv import load_dotenv

# Google ADK imports
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

# Import subagents
from .subagents.rate_limit import DEFAULT_RETRY_CONFIG
from .subagents.research_advisor import create_research_advisor_agent
from .subagents.article_analyzer import create_article_analyzer_agent
from .subagents.validator import create_validator_agent
from .subagents.instructions.maestro_router_instruction import MAESTRO_ROUTER_INSTRUCTION

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


# =============================================================================
# MAESTRO ORCHESTRATOR AGENT
# =============================================================================

class MaestroAgent(BaseAgent):
    """
    Sequential orchestrator agent for systematic literature review.
    
    This agent manages a three-stage workflow:
    
    STAGE 1: Research Questions (Belo-like)
    - Ask user what they want to research
    - Generate research questions
    - Let user select questions
    
    STAGE 2: Article Analysis (Zebra-like)
    - Ask if user has articles/PDFs
    - If no, search Google for articles
    - Analyze articles with TRUE/FALSE classifications
    - Create results table
    
    STAGE 3: Validation & Summary (Cross-like)
    - Ask if user has reference table
    - If yes, compare and calculate metrics
    - Provide comprehensive summary
    
    Uses LLM-based routing and interactive conversation at each stage.
    """
    
    # Pydantic field declarations for sub-agents
    router: LlmAgent
    research_advisor: LlmAgent
    article_analyzer: LlmAgent
    validator: LlmAgent
    
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, name: str = "maestro_agent"):
        """Initialize the MaestroAgent orchestrator with its subagents."""
        
        # Router agent - determines current workflow stage
        router = LlmAgent(
            name="router",
            model=Gemini(model=GEMINI_MODEL),
            instruction=MAESTRO_ROUTER_INSTRUCTION,
            output_key="current_stage",
            generate_content_config=DEFAULT_RETRY_CONFIG,
        )
        
        # Stage 1: Research Advisor (Belo-like)
        research_advisor = create_research_advisor_agent()
        
        # Stage 2: Article Analyzer (Zebra-like)
        article_analyzer = create_article_analyzer_agent()
        
        # Stage 3: Validator (Cross-like)
        validator = create_validator_agent()
        
        # Initialize BaseAgent with subagents list
        super().__init__(
            name=name,
            router=router,
            research_advisor=research_advisor,
            article_analyzer=article_analyzer,
            validator=validator,
            sub_agents=[router, research_advisor, article_analyzer, validator],
        )
        
        logger.info(f"✅ MaestroAgent orchestrator '{name}' initialized")
        logger.info("   Sequential workflow stages:")
        logger.info("   1. research_advisor: Formulate research questions")
        logger.info("   2. article_analyzer: Analyze articles (TRUE/FALSE)")
        logger.info("   3. validator: Validate and summarize results")
    
    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Custom sequential orchestration logic.
        
        The workflow proceeds through three stages:
        1. Research question formulation
        2. Article analysis
        3. Validation and summary
        
        Each stage waits for appropriate user input before proceeding.
        """
        logger.info(f"[{self.name}] Processing request...")
        
        # Step 1: Determine current stage using router
        logger.info(f"[{self.name}] Running router to determine current stage...")
        async for event in self.router.run_async(ctx):
            yield event
        
        # Get the current stage from state
        current_stage = ctx.session.state.get("current_stage", "").strip().lower()
        logger.info(f"[{self.name}] Current stage: {current_stage}")
        
        # Route to appropriate subagent based on stage
        if "research_questions" in current_stage or not current_stage:
            # Stage 1: Research Question Formulation
            logger.info(f"[{self.name}] Stage 1: Running research_advisor...")
            async for event in self.research_advisor.run_async(ctx):
                yield event
            
            # Check if questions were selected - if so, proceed to next stage
            selected = ctx.session.state.get("selected_questions", [])
            if selected:
                logger.info(f"[{self.name}] Questions selected, proceeding to article analysis...")
                ctx.session.state["current_stage"] = "article_analysis"
                async for event in self.article_analyzer.run_async(ctx):
                    yield event
        
        elif "article_analysis" in current_stage:
            # Stage 2: Article Analysis
            logger.info(f"[{self.name}] Stage 2: Running article_analyzer...")
            async for event in self.article_analyzer.run_async(ctx):
                yield event
            
            # Check if analysis is complete - if so, proceed to validation
            results = ctx.session.state.get("analysis_results", None)
            if results:
                logger.info(f"[{self.name}] Analysis complete, proceeding to validation...")
                ctx.session.state["current_stage"] = "validation"
                async for event in self.validator.run_async(ctx):
                    yield event
        
        elif "validation" in current_stage:
            # Stage 3: Validation and Summary
            logger.info(f"[{self.name}] Stage 3: Running validator...")
            async for event in self.validator.run_async(ctx):
                yield event
        
        else:
            # Default: Start with research advisor
            logger.info(f"[{self.name}] Unknown stage, starting with research_advisor...")
            async for event in self.research_advisor.run_async(ctx):
                yield event
        
        logger.info(f"[{self.name}] Stage complete.")


def create_maestro_agent():
    """
    Creates and returns the MaestroAgent orchestrator instance.
    
    Returns:
        MaestroAgent: The orchestrator agent
    """
    agent = MaestroAgent(name="maestro_agent")
    print("✅ Maestro Sequential Agent created with stages:")
    print("   1. research_advisor: Formulate research questions (Belo-like)")
    print("   2. article_analyzer: Analyze articles with TRUE/FALSE (Zebra-like)")
    print("   3. validator: Validate and summarize results (Cross-like)")
    return agent


async def _run_agent_async(prompt: str, max_retries: int = 3):
    """Run the agent asynchronously with retry handling."""
    agent = create_maestro_agent()
    runner = InMemoryRunner(agent=agent)
    print("✅ Runner created.")
    
    for attempt in range(max_retries):
        try:
            response = await runner.run_debug(prompt)
            return response
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                wait_time = 60
                if "retry in" in error_msg.lower():
                    import re
                    match = re.search(r'retry in (\d+\.?\d*)s', error_msg.lower())
                    if match:
                        wait_time = float(match.group(1)) + 5
                
                print(f"⏳ Rate limited. Waiting {wait_time:.0f} seconds before retry {attempt + 1}/{max_retries}...")
                await asyncio.sleep(wait_time)
            else:
                raise e
    
    raise Exception(f"Max retries ({max_retries}) exceeded due to rate limiting")


def simple_llm(prompt: str) -> str:
    """
    A simple LLM function that uses the Maestro Agent via InMemoryRunner.
    """
    return str(asyncio.run(_run_agent_async(prompt)))


def run_literature_review(topic: str) -> str:
    """
    Start a systematic literature review workflow.
    
    This function initiates the three-stage Maestro workflow:
    1. Generate research questions for the topic
    2. Analyze articles (user will be asked for PDFs or search)
    3. Validate and summarize results
    
    Args:
        topic: The research topic to explore.
    
    Returns:
        The agent's response.
    """
    prompt = f"""I want to conduct a systematic literature review on: {topic}

Please help me:
1. First, suggest some focused research questions I can explore
2. Make sure the questions can be answered with TRUE/FALSE when analyzing papers
3. Let me know how many questions you can provide"""
    
    return simple_llm(prompt)


# =============================================================================
# EXPORT FOR ADK WEB
# =============================================================================
# This is required for `adk web agents/maestro` to find the agent
root_agent = create_maestro_agent()


if __name__ == "__main__":
    # Example usage
    try:
        if len(sys.argv) >= 2:
            # User provided a topic or query
            user_input = " ".join(sys.argv[1:])
            
            print(f"\n--- Maestro Sequential Agent ---")
            print(f"Input: {user_input}")
            print("\nStarting workflow...")
            
            result = simple_llm(user_input)
            print(f"\nResponse:\n{result}")
        
        else:
            # No arguments - show usage
            print("\n" + "="*70)
            print("  MAESTRO - Sequential Literature Review Agent")
            print("="*70)
            print("\nA three-stage agent that helps you conduct systematic literature reviews.")
            print("\n📋 WORKFLOW STAGES:")
            print("\n  STAGE 1: Research Question Formulation (Belo-like)")
            print("    - Describe your research topic")
            print("    - Receive up to 10 research questions")
            print("    - Select which questions to explore")
            print("\n  STAGE 2: Article Analysis (Zebra-like)")
            print("    - Provide your articles/PDFs OR")
            print("    - Let the agent search Google for relevant papers")
            print("    - Each article is analyzed for each question")
            print("    - Results are TRUE/FALSE classifications")
            print("\n  STAGE 3: Validation & Summary (Cross-like)")
            print("    - Optionally provide a reference table for comparison")
            print("    - Get Cohen's Kappa and agreement metrics")
            print("    - Receive comprehensive summary and recommendations")
            print("\n📝 USAGE:")
            print('  python -m agents.maestro.agent "your research topic"')
            print('  python -m agents.maestro.agent "I want to study machine learning in healthcare"')
            print('  python -m agents.maestro.agent "help me review papers on climate change"')
            print("\n🌐 OR use with ADK Web:")
            print("  adk web agents/maestro")
            print("="*70)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
