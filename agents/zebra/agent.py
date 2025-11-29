"""
Zebra LLM Agent - Orchestrator for Systematic Literature Review

This is the main orchestrator agent that:
1. Routes requests to appropriate subagents using an LLM router
2. Handles paper classification workflows (sequential: classify -> update Excel)
3. Coordinates direct Excel operations (delete columns, update cells, etc.)
4. Manages PDF reading operations

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
from .subagents.paper_classifier import create_paper_classifier_agent
from .subagents.excel_handler import create_excel_handler_agent
from .subagents.summarizer import create_summarizer_agent
from .subagents.instructions.router_instruction import ROUTER_INSTRUCTION

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


# =============================================================================
# ZEBRA ORCHESTRATOR AGENT
# =============================================================================

class ZebraAgent(BaseAgent):
    """
    Orchestrator agent for systematic literature review.
    
    This agent routes requests to appropriate subagents:
    - router: Determines what type of request (classify/excel/pdf)
    - paper_classifier: For PDF reading and paper classification
    - excel_handler: For Excel operations (delete, update, etc.)
    - summarizer: For providing final response to user
    
    Uses LLM-based routing for intelligent request classification.
    """
    
    # Pydantic field declarations for sub-agents
    router: LlmAgent
    paper_classifier: LlmAgent
    excel_handler: LlmAgent
    summarizer: LlmAgent
    
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, name: str = "zebra_llm_agent"):
        """Initialize the ZebraAgent orchestrator with its subagents."""
        
        # Router agent - determines what type of request this is
        router = LlmAgent(
            name="router",
            model=Gemini(model=GEMINI_MODEL),
            instruction=ROUTER_INSTRUCTION,
            output_key="request_type",
            generate_content_config=DEFAULT_RETRY_CONFIG,
        )
        
        # Import subagents
        paper_classifier = create_paper_classifier_agent()
        excel_handler = create_excel_handler_agent()
        summarizer = create_summarizer_agent()
        
        # Initialize BaseAgent with subagents list
        super().__init__(
            name=name,
            router=router,
            paper_classifier=paper_classifier,
            excel_handler=excel_handler,
            summarizer=summarizer,
            sub_agents=[router, paper_classifier, excel_handler, summarizer],
        )
        
        logger.info(f"✅ ZebraAgent orchestrator '{name}' initialized with subagents: router, paper_classifier, excel_handler, summarizer")
    
    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Custom orchestration logic.
        
        1. Route the request using LLM to determine type(s)
        2. Execute each type in sequence (supports multi-step workflows)
        3. For classify requests, always follow up with excel_handler to save results
        4. Run summarizer to provide final response
        """
        logger.info(f"[{self.name}] Processing request...")
        
        # Step 1: Route the request using LLM
        logger.info(f"[{self.name}] Running router to determine request type...")
        async for event in self.router.run_async(ctx):
            yield event
        
        # Get the request type(s) from state - can be comma-separated
        request_type_raw = ctx.session.state.get("request_type", "").strip().lower()
        logger.info(f"[{self.name}] Request type(s): {request_type_raw}")
        
        # Parse multiple request types (e.g., "classify,excel" or "pdf,excel")
        request_types = [rt.strip() for rt in request_type_raw.split(",") if rt.strip()]
        
        if not request_types:
            request_types = ["excel"]  # Default fallback
        
        # Step 2: Execute each workflow step in sequence
        executed_classify = False
        for i, request_type in enumerate(request_types):
            logger.info(f"[{self.name}] Step {i+1}/{len(request_types)}: {request_type}")
            
            if "classify" in request_type:
                logger.info(f"[{self.name}] Routing to paper_classifier...")
                async for event in self.paper_classifier.run_async(ctx):
                    yield event
                executed_classify = True
            elif "excel" in request_type:
                logger.info(f"[{self.name}] Routing to excel_handler...")
                async for event in self.excel_handler.run_async(ctx):
                    yield event
            elif "pdf" in request_type:
                # For PDF-only requests, use paper_classifier (it has the PDF tools)
                logger.info(f"[{self.name}] Routing to paper_classifier for PDF reading...")
                async for event in self.paper_classifier.run_async(ctx):
                    yield event
            else:
                # Default: try excel_handler for general queries
                logger.info(f"[{self.name}] Unknown type '{request_type}', defaulting to excel_handler...")
                async for event in self.excel_handler.run_async(ctx):
                    yield event
        
        # Step 3: If we classified but didn't explicitly run excel, run it now to save results
        if executed_classify and "excel" not in request_types:
            logger.info(f"[{self.name}] Auto-routing to excel_handler to save classification results...")
            async for event in self.excel_handler.run_async(ctx):
                yield event
        
        # Step 4: Run summarizer to provide final response to user
        logger.info(f"[{self.name}] Running summarizer to provide final response...")
        async for event in self.summarizer.run_async(ctx):
            yield event
        
        logger.info(f"[{self.name}] All steps completed.")


def create_zebra_llm_agent():
    """
    Creates and returns the ZebraAgent orchestrator instance.
    
    Returns:
        ZebraAgent: The orchestrator agent
    """
    agent = ZebraAgent(name="zebra_llm_agent")
    print("✅ Zebra Orchestrator Agent created with subagents:")
    print("   - router: Determines request type (classify/excel/pdf)")
    print("   - paper_classifier: Reads PDFs and classifies papers")
    print("   - excel_handler: Excel operations (delete, update, etc.)")
    print("   - summarizer: Provides final response to user")
    return agent

async def _run_agent_async(prompt: str, max_retries: int = 3):
    agent = create_zebra_llm_agent()
    runner = InMemoryRunner(agent=agent)
    print("✅ Runner created.")
    
    for attempt in range(max_retries):
        try:
            response = await runner.run_debug(prompt)
            return response
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                # Extract retry delay if available
                wait_time = 60  # default wait time
                if "retry in" in error_msg.lower():
                    import re
                    match = re.search(r'retry in (\d+\.?\d*)s', error_msg.lower())
                    if match:
                        wait_time = float(match.group(1)) + 5  # Add buffer
                
                print(f"⏳ Rate limited. Waiting {wait_time:.0f} seconds before retry {attempt + 1}/{max_retries}...")
                await asyncio.sleep(wait_time)
            else:
                raise e
    
    raise Exception(f"Max retries ({max_retries}) exceeded due to rate limiting")

def simple_llm(prompt: str) -> str:
    """
    A simple LLM function that uses the Zebra LLM Agent via InMemoryRunner.
    """
    return str(asyncio.run(_run_agent_async(prompt)))

def llm_reviewer(articles_dir: str, excel_path: str, user_query: str) -> str:
    """
    Run the zebra agent to classify papers based on a natural language query.
    
    The agent will interpret the user's query to understand what criterion to classify,
    determine an appropriate column name, and classify all papers accordingly.
    
    Args:
        articles_dir: Path to the directory containing PDF articles.
        excel_path: Path to the Excel file to update.
        user_query: Natural language description of what to classify 
                   (e.g., "find papers about regression testing", 
                    "check for conformance", "which papers discuss API testing")
    
    Returns:
        The agent's response with classification results.
    
    Examples:
        >>> llm_reviewer("test/Articles", "test/table_1.xlsx", "find regression testing papers")
        >>> llm_reviewer("test/Articles", "test/table_1.xlsx", "which papers discuss conformance?")
        >>> llm_reviewer("test/Articles", "test/table_1.xlsx", "check for API testing coverage")
        >>> llm_reviewer("test/Articles", "test/table_1.xlsx", "do these papers cover security testing?")
    """
    prompt = f"""I need you to analyze research papers and classify them based on my research question.

**Articles Directory:** {articles_dir}
**Excel File:** {excel_path}

**My Research Question/Guideline:**
{user_query}

Please:
1. Understand what criterion I want to classify from my question above
2. Determine an appropriate column name for the Excel file
3. Read all PDF papers in the articles directory
4. For each paper, determine if it discusses this criterion (True/False)
5. Match papers to the Excel rows by title and update the classification column
6. Provide a summary of your findings

Remember to create the column if it doesn't exist."""
    
    return simple_llm(prompt)

# Backward compatibility aliases
def run_regression_classification(articles_dir: str, excel_path: str) -> str:
    """Legacy function for regression classification."""
    return llm_reviewer(articles_dir, excel_path, "Find papers that discuss regression testing")

def run_classification(articles_dir: str, excel_path: str, criterion: str) -> str:
    """
    Convenience function with explicit criterion name.
    """
    return llm_reviewer(articles_dir, excel_path, f"Find papers that discuss {criterion}")


# =============================================================================
# EXPORT FOR ADK WEB
# =============================================================================
# This is required for `adk web agents` to find the agent
root_agent = create_zebra_llm_agent()


if __name__ == "__main__":
    # Example usage
    try:
        if len(sys.argv) >= 4:
            # Full arguments: articles_dir, excel_path, user_query
            articles_dir = sys.argv[1]
            excel_path = sys.argv[2]
            user_query = " ".join(sys.argv[3:])  # Join all remaining args as the query
            
            print(f"\n--- Zebra LLM Reviewer ---")
            print(f"Articles: {articles_dir}")
            print(f"Excel: {excel_path}")
            print(f"Query: {user_query}")
            
            if not os.path.exists(articles_dir):
                raise ValueError(f"Articles directory not found: {articles_dir}")
            if not os.path.exists(excel_path):
                raise ValueError(f"Excel file not found: {excel_path}")
            
            result = llm_reviewer(articles_dir, excel_path, user_query)
            print(f"\nResponse:\n{result}")
        
        elif len(sys.argv) >= 2:
            # User query with default paths
            user_query = " ".join(sys.argv[1:])
            articles_dir = "test/Articles"
            excel_path = "test/table_1.xlsx"
            
            # Check if it's a PDF file
            if len(sys.argv) == 2 and sys.argv[1].lower().endswith('.pdf'):
                print("\n--- PDF Analysis ---")
                user_prompt = f"Read and summarize this PDF: {sys.argv[1]}"
                print(f"Analyzing: {sys.argv[1]}")
                result = simple_llm(user_prompt)
                print(f"\nResponse:\n{result}")
            else:
                print(f"\n--- Zebra LLM Reviewer ---")
                print(f"Articles: {articles_dir}")
                print(f"Excel: {excel_path}")
                print(f"Query: {user_query}")
                
                if not os.path.exists(articles_dir):
                    raise ValueError(f"Articles directory not found: {articles_dir}")
                if not os.path.exists(excel_path):
                    raise ValueError(f"Excel file not found: {excel_path}")
                
                result = llm_reviewer(articles_dir, excel_path, user_query)
                print(f"\nResponse:\n{result}")
        
        else:
            # No arguments - show usage and examples
            print("\n" + "="*60)
            print("  ZEBRA LLM REVIEWER - Paper Classification Agent")
            print("="*60)
            print("\nClassify research papers using natural language queries.")
            print("\nUSAGE:")
            print("  python -m agents.zebra.agent <your question>")
            print("  python -m agents.zebra.agent <articles_dir> <excel_path> <your question>")
            print("\nEXAMPLES:")
            print('  python -m agents.zebra.agent "find papers about regression testing"')
            print('  python -m agents.zebra.agent "which papers discuss conformance?"')
            print('  python -m agents.zebra.agent "check for API testing"')
            print('  python -m agents.zebra.agent "do these cover security testing?"')
            print('  python -m agents.zebra.agent "find mutation testing papers"')
            print('  python -m agents.zebra.agent "papers using model-based testing"')
            print("\nFULL PATH EXAMPLE:")
            print('  python -m agents.zebra.agent test/Articles test/table_1.xlsx "find performance testing"')
            print("\nThe agent will:")
            print("  1. Understand your research question")
            print("  2. Determine the classification criterion")
            print("  3. Create/update the appropriate Excel column")
            print("  4. Classify each paper as True/False")
            print("  5. Provide evidence for each classification")
            print("="*60)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
