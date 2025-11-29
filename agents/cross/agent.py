"""
Cross Agent - Orchestrator for Table Comparison

This is the main orchestrator agent that:
1. Routes requests to appropriate subagents
2. Handles table comparison workflows
3. Provides statistical analysis results

Uses Google ADK's BaseAgent pattern with _run_async_impl for custom orchestration.
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
from .subagents.cross_comparison import create_cross_comparison_agent
from .subagents.summarizer import create_cross_summarizer_agent
from .subagents.instructions.cross_router_instruction import CROSS_ROUTER_INSTRUCTION

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


# =============================================================================
# CROSS ORCHESTRATOR AGENT
# =============================================================================

class CrossAgent(BaseAgent):
    """
    Orchestrator agent for table comparison.
    
    This agent routes requests to appropriate subagents:
    - router: Determines what type of request (compare/info)
    - cross_comparison: For table comparison and statistics
    - summarizer: For providing final response to user
    
    Uses LLM-based routing for intelligent request classification.
    """
    
    # Pydantic field declarations for sub-agents
    router: LlmAgent
    cross_comparison: LlmAgent
    summarizer: LlmAgent
    
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, name: str = "cross_agent"):
        """Initialize the CrossAgent orchestrator with its subagents."""
        
        # Router agent - determines what type of request this is
        router = LlmAgent(
            name="router",
            model=Gemini(model=GEMINI_MODEL),
            instruction=CROSS_ROUTER_INSTRUCTION,
            output_key="request_type",
            generate_content_config=DEFAULT_RETRY_CONFIG,
        )
        
        # Import subagents
        cross_comparison = create_cross_comparison_agent()
        summarizer = create_cross_summarizer_agent()
        
        # Initialize BaseAgent with subagents list
        super().__init__(
            name=name,
            router=router,
            cross_comparison=cross_comparison,
            summarizer=summarizer,
            sub_agents=[router, cross_comparison, summarizer],
        )
        
        logger.info(f"✅ CrossAgent orchestrator '{name}' initialized with subagents: router, cross_comparison, summarizer")
    
    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Custom orchestration logic.
        
        1. Route the request using LLM to determine type
        2. Execute appropriate subagent
        3. Run summarizer to provide final response
        """
        logger.info(f"[{self.name}] Processing request...")
        
        # Step 1: Route the request using LLM
        logger.info(f"[{self.name}] Running router to determine request type...")
        async for event in self.router.run_async(ctx):
            yield event
        
        # Get the request type from state
        request_type = ctx.session.state.get("request_type", "").strip().lower()
        logger.info(f"[{self.name}] Request type: {request_type}")
        
        # Step 2: Execute comparison (most requests will be comparisons)
        logger.info(f"[{self.name}] Routing to cross_comparison...")
        async for event in self.cross_comparison.run_async(ctx):
            yield event
        
        # Step 3: Run summarizer to provide final response
        logger.info(f"[{self.name}] Running summarizer to provide final response...")
        async for event in self.summarizer.run_async(ctx):
            yield event
        
        logger.info(f"[{self.name}] All steps completed.")


def create_cross_agent():
    """
    Creates and returns the CrossAgent orchestrator instance.
    
    Returns:
        CrossAgent: The orchestrator agent
    """
    agent = CrossAgent(name="cross_agent")
    print("✅ Cross Comparison Agent created with subagents:")
    print("   - router: Determines request type (compare/info)")
    print("   - cross_comparison: Table comparison and statistics")
    print("   - summarizer: Provides final response to user")
    return agent


async def _run_agent_async(prompt: str, max_retries: int = 3):
    agent = create_cross_agent()
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


def compare_tables(
    table1_path: str,
    table2_path: str,
    columns: str,
    match_by: str = "Title"
) -> str:
    """
    Compare two tables and get statistical analysis.
    
    Args:
        table1_path: Path to the first Excel file.
        table2_path: Path to the second Excel file.
        columns: Comma-separated column names to compare.
        match_by: Column to match rows by (default: "Title").
    
    Returns:
        Statistical comparison results.
    """
    prompt = f"""Compare these two tables:
- Table 1: {table1_path}
- Table 2: {table2_path}

Compare these columns: {columns}
Match rows by: {match_by}

Provide full statistical analysis including:
1. Agreement rates for each column
2. Cohen's Kappa with interpretation
3. List of disagreements"""
    
    return str(asyncio.run(_run_agent_async(prompt)))


# =============================================================================
# EXPORT FOR ADK WEB
# =============================================================================
root_agent = create_cross_agent()


if __name__ == "__main__":
    try:
        if len(sys.argv) >= 4:
            # Arguments: table1, table2, columns
            table1 = sys.argv[1]
            table2 = sys.argv[2]
            columns = sys.argv[3]
            match_by = sys.argv[4] if len(sys.argv) > 4 else "Title"
            
            print(f"\n--- Cross Comparison Agent ---")
            print(f"Table 1: {table1}")
            print(f"Table 2: {table2}")
            print(f"Columns: {columns}")
            print(f"Match by: {match_by}")
            
            result = compare_tables(table1, table2, columns, match_by)
            print(f"\nResults:\n{result}")
        
        elif len(sys.argv) >= 2:
            # Free-form query
            query = " ".join(sys.argv[1:])
            print(f"\n--- Cross Comparison Agent ---")
            print(f"Query: {query}")
            
            result = asyncio.run(_run_agent_async(query))
            print(f"\nResults:\n{result}")
        
        else:
            print("\n" + "="*60)
            print("  CROSS COMPARISON AGENT - Table Comparison Tool")
            print("="*60)
            print("\nCompare two Excel tables and get statistical analysis.")
            print("\nUSAGE:")
            print("  python -m agents.cross.agent <table1> <table2> <columns> [match_by]")
            print("  python -m agents.cross.agent <your question>")
            print("\nEXAMPLES:")
            print('  python -m agents.cross.agent data/01/table_1.xlsx data/02/table_1.xlsx "Software,Testing"')
            print('  python -m agents.cross.agent "compare Software column between data/01 and data/02"')
            print('  python -m agents.cross.agent "calculate Cohen\'s Kappa for Regression"')
            print("\nThe agent will provide:")
            print("  - Agreement rates (percentage)")
            print("  - Cohen's Kappa (inter-rater reliability)")
            print("  - Disagreement details")
            print("  - Statistical interpretation")
            print("="*60)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
