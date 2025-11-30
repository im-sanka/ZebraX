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
import re
import json
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

# Import Excel tools for direct use
from .subagents.tools.excel_tools import update_classification_by_title

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model constant
GEMINI_MODEL = "gemini-2.5-flash"


def _extract_json_from_text(text: str) -> dict:
    """Extract JSON object from text that may contain markdown or other content."""
    # Try to find JSON in code blocks first (greedy match for nested objects)
    json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON that starts with { and contains "criterion" - use greedy match
    # Look for the outermost JSON object containing our expected keys
    json_match = re.search(r'(\{[^{}]*"criterion".*"classifications"\s*:\s*\[.*?\]\s*,?\s*"summary".*?\})', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find any JSON object that spans from first { to last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        potential_json = text[first_brace:last_brace + 1]
        try:
            return json.loads(potential_json)
        except json.JSONDecodeError:
            pass
    
    # Try to parse the entire text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    return None


def _extract_excel_path_from_prompt(prompt: str) -> str:
    """Extract Excel file path from the user's prompt."""
    # Look for common patterns
    patterns = [
        r'excel[_ ]?(?:file|path)?[:\s]+["\']?([^\s"\']+\.xlsx?)["\']?',
        r'["\']([^\s"\']+\.xlsx?)["\']',
        r'(\S+\.xlsx?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


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
        
        # Step 3: If we classified, directly save results to Excel
        if executed_classify:
            logger.info(f"[{self.name}] Saving classification results to Excel...")
            
            # Get the classification result from state (this is the LLM's text output)
            classification_result_text = ctx.session.state.get("classification_result", "")
            logger.info(f"[{self.name}] Classification result text length: {len(classification_result_text) if classification_result_text else 0}")
            
            if classification_result_text:
                # Try to extract JSON from the classification result
                logger.info(f"[{self.name}] Attempting to extract JSON from classification result...")
                classification_data = _extract_json_from_text(classification_result_text)
                
                if classification_data:
                    logger.info(f"[{self.name}] ✅ Parsed classification data successfully")
                    logger.info(f"[{self.name}] Keys found: {list(classification_data.keys())}")
                    
                    # Extract the required fields
                    criterion = classification_data.get("criterion", "Classification")
                    excel_path = classification_data.get("excel_path", "")
                    classifications = classification_data.get("classifications", [])
                    logger.info(f"[{self.name}] Criterion: {criterion}, Excel: {excel_path}, Classifications: {len(classifications)}")
                    
                    # If no excel_path in the result, try to extract from original prompt
                    if not excel_path:
                        # Get original user message from session
                        user_messages = [e for e in ctx.session.events if hasattr(e, 'content')]
                        if user_messages:
                            original_prompt = str(user_messages[0].content) if user_messages else ""
                            excel_path = _extract_excel_path_from_prompt(original_prompt)
                    
                    # Default path if still not found
                    if not excel_path:
                        excel_path = "test/table_1.xlsx"
                    
                    if classifications:
                        logger.info(f"[{self.name}] Updating Excel file: {excel_path}")
                        logger.info(f"[{self.name}] Column: {criterion}, Papers: {len(classifications)}")
                        
                        # Directly call the Excel update tool
                        try:
                            result = update_classification_by_title(
                                file_path=excel_path,
                                classifications=classifications,
                                column_name=criterion,
                                title_column="Title",
                                add_missing_rows=True
                            )
                            
                            # Store the result in state for the summarizer
                            ctx.session.state["excel_result"] = str(result)
                            logger.info(f"[{self.name}] Excel update result: {result.get('message', 'Unknown')}")
                            
                            if result.get("success"):
                                matched = result.get("matched_count", 0)
                                added = result.get("added_count", 0)
                                logger.info(f"[{self.name}] ✅ Excel updated: {matched} matched, {added} added as new rows")
                            else:
                                logger.error(f"[{self.name}] ❌ Excel update failed: {result.get('error', 'Unknown error')}")
                        except Exception as e:
                            logger.error(f"[{self.name}] ❌ Exception during Excel update: {str(e)}")
                            ctx.session.state["excel_result"] = f"Error: {str(e)}"
                    else:
                        logger.warning(f"[{self.name}] No classifications found in the result")
                else:
                    logger.warning(f"[{self.name}] Could not parse JSON from classification result")
                    logger.warning(f"[{self.name}] First 500 chars: {classification_result_text[:500] if classification_result_text else 'EMPTY'}")
                    # Fall back to LLM-based excel handler
                    logger.info(f"[{self.name}] Falling back to excel_handler agent...")
                    async for event in self.excel_handler.run_async(ctx):
                        yield event
            else:
                logger.warning(f"[{self.name}] No classification_result in session state")
        
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
