import os
# Ensure google-adk is installed: pip install google-adk
from google.adk.agents import Agent, ParallelAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Simple fallback to load .env if python-dotenv is not installed
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"').strip("'")

def create_zebra_agent():
    """Creates and returns the root agent (Zebra Agent) with the simplified workflow."""
    
    # --- 1. Article Search Agent ---
    search_agent = Agent(
        name="ArticleSearchAgent",
        model=Gemini(model="gemini-2.5-flash"),
        description="Searches for scientific articles using Google Search.",
        instruction="""You are a Scientific Librarian. 
        Use Google Search to find scientific articles relevant to the user's query.
        
        Output Format:
        Return the findings in a structured table with columns: 'Title', 'Abstract', and 'DOI_URL'.
        
        Quantity Rules:
        - If the user does not specify a number, provide exactly 5 articles.
        - If the user specifies a number, use that number, but NEVER exceed 10 articles.
        - If the user requests more than 10, provide exactly 10.""",
        tools=[google_search]
    )

    # --- 2. Analysis Sub-Agents ---
    
    # Sub-agent A: Data Extractor
    extractor_agent = Agent(
        name="DataExtractor",
        model=Gemini(model="gemini-2.5-flash"),
        description="Extracts methodologies and qualitative findings from text.",
        instruction="""You are a Data Extractor. 
        Analyze the provided article details. Extract key methodologies, hypotheses, and qualitative findings.""",
    )

    # Sub-agent B: Image/Figure Analysis (Text-based for now)
    image_analysis_agent = Agent(
        name="ImageAnalyzer",
        model=Gemini(model="gemini-2.5-flash"),
        description="Analyzes descriptions of figures and visual data.",
        instruction="""You are an Image & Figure Analyst. 
        Analyze any descriptions of figures, charts, or visual data present in the article summary. 
        Infer the type of visual evidence used (e.g., bar charts, heatmaps, microscopy images).""",
    )

    # Sub-agent C: Data Analysis
    data_analysis_agent = Agent(
        name="DataAnalyzer",
        model=Gemini(model="gemini-2.5-flash"),
        description="Identifies quantitative data and statistical metrics.",
        instruction="""You are a Statistical Analyst. 
        Identify any quantitative data, sample sizes, p-values, or performance metrics mentioned in the article details.""",
    )

    # Group them into a Parallel Team
    analysis_team = ParallelAgent(
        name="ArticleAnalysisTeam",
        sub_agents=[extractor_agent, image_analysis_agent, data_analysis_agent],
        description="Analyzes scientific articles in parallel (Extraction, Figures, Stats)."
    )

    # --- 3. Root Agent (Orchestrator) ---
    root_agent = Agent(
        name="ZebraOrchestrator",
        model=Gemini(model="gemini-2.5-pro"),
        description="Orchestrates the systematic review process: searching, analyzing, and tabulating results.",
        instruction="""You are the Zebra Orchestrator. Your goal is to produce a comprehensive tabulated report.

        Your team consists of:
        1. 'ArticleSearchAgent': Finds scientific articles.
        2. 'ArticleAnalysisTeam': Analyzes article details (methodology, figures, stats).

        Workflow:
        1. Delegate to 'ArticleSearchAgent' to find relevant articles.
        2. Once you receive the list of articles, for EACH article, delegate to 'ArticleAnalysisTeam' to analyze it. Pass the article's Title and Abstract.
        3. Compile all the analyzed data into a single, well-structured table that answers the user's original question.
        """,
        sub_agents=[search_agent, analysis_team]
    )
    
    print("✅ Zebra Agent (Simplified Orchestrator) defined.")
    return root_agent

# Expose the agent for ADK
root_agent = create_zebra_agent()

if __name__ == "__main__":
    async def run_demo():
        print("--- Starting Zebra Agent Trace Demo ---")
        
        # 1. Setup Session
        session_service = InMemorySessionService()
        APP_NAME = "zebra_research_app"
        USER_ID = "researcher_1"
        SESSION_ID = "session_trace_001"
        
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID
        )
        print(f"✅ Session created: {SESSION_ID}")

        # 2. Setup Runner
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service
        )
        print(f"✅ Runner created for: {runner.agent.name}")

        # 3. Interaction Loop with Trace
        async def call_agent_with_trace(query: str):
            print(f"\n>>> 👤 User Query: {query}")
            content = types.Content(role='user', parts=[types.Part(text=query)])
            
            print("--- 🕵️‍♂️ Execution Trace ---")
            async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
                # Print event details for tracing
                event_type = type(event).__name__
                print(f"  [Event] Type: {event_type} | Author: {event.author}")
                
                # Show content if available
                if hasattr(event, 'content') and event.content:
                    # Truncate long content for readability in trace
                    content_str = str(event.content)
                    if len(content_str) > 200:
                        content_str = content_str[:200] + "..."
                    print(f"          Content: {content_str}")
                
                # Show tool calls if available
                if hasattr(event, 'tool_calls') and event.tool_calls:
                    print(f"          🛠️ Tool Call: {event.tool_calls}")

                if event.is_final_response():
                    print("--- End of Trace ---")
                    if event.content and event.content.parts:
                        print(f"\n<<< 🦓 Agent Response:\n{event.content.parts[0].text}")
                    break

        # 4. Run a test query
        await call_agent_with_trace("Find 3 articles about 'CRISPR in agriculture' and analyze them.")

    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nStopped by user.")
