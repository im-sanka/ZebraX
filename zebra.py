import os
import asyncio
from dotenv import load_dotenv
# Ensure google-adk is installed: pip install google-adk
from google.adk.agents import Agent, ParallelAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, google_search

# Load environment variables from .env file
load_dotenv()

def create_zebra_agent():
    """Creates and returns the root agent (Zebra Agent) with the simplified workflow."""
    
    # --- 1. Article Search Agent ---
    search_agent = Agent(
        name="ArticleSearchAgent",
        model=Gemini(model="gemini-2.5-flash"),
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
        instruction="""You are a Data Extractor. 
        Analyze the provided article details. Extract key methodologies, hypotheses, and qualitative findings.""",
    )

    # Sub-agent B: Image/Figure Analysis (Text-based for now)
    image_analysis_agent = Agent(
        name="ImageAnalyzer",
        model=Gemini(model="gemini-2.5-flash"),
        instruction="""You are an Image & Figure Analyst. 
        Analyze any descriptions of figures, charts, or visual data present in the article summary. 
        Infer the type of visual evidence used (e.g., bar charts, heatmaps, microscopy images).""",
    )

    # Sub-agent C: Data Analysis
    data_analysis_agent = Agent(
        name="DataAnalyzer",
        model=Gemini(model="gemini-2.5-flash"),
        instruction="""You are a Statistical Analyst. 
        Identify any quantitative data, sample sizes, p-values, or performance metrics mentioned in the article details.""",
    )

    # Group them into a Parallel Team
    analysis_team = ParallelAgent(
        name="ArticleAnalysisTeam",
        sub_agents=[extractor_agent, image_analysis_agent, data_analysis_agent],
    )

    # --- 3. Root Agent (Orchestrator) ---
    root_agent = Agent(
        name="ZebraOrchestrator",
        model=Gemini(model="gemini-2.5-pro"),
        instruction="""You are the Zebra Orchestrator. Your goal is to produce a comprehensive tabulated report.

        FOLLOW THESE STEPS STRICTLY:
        1. Call `ArticleSearchAgent` to find scientific articles related to the user's question.
        2. Once you have the list of articles (which will be a table), you MUST loop through EACH article in the list.
        3. For EACH article, call the `ArticleAnalysisTeam` tool. Pass the specific article's details (Title + Abstract) as the input.
        4. Collect the outputs from the analysis team for all articles.
        5. Finally, compile all the analyzed data into a single, well-structured table that answers the user's original question.
        """,
        tools=[
            AgentTool(search_agent), 
            AgentTool(analysis_team)
        ],
    )
    
    print("✅ Zebra Agent (Simplified Orchestrator) defined.")
    return root_agent

async def _run_agent_async(prompt: str):
    agent = create_zebra_agent()
    runner = InMemoryRunner(agent=agent)
    print("✅ Runner created.")
    response = await runner.run_debug(prompt)
    return response

def zebra_llm(prompt: str) -> str:
    """
    A simple LLM function that uses the Zebra Agent via InMemoryRunner.
    """
    return str(asyncio.run(_run_agent_async(prompt)))

if __name__ == "__main__":
    # Example usage
    try:
        print("\n--- Test: Synthetic Biology ---")
        user_prompt = "What are the latest advancements in synthetic biology?"
        print(f"Sending prompt: {user_prompt}")
        result = zebra_llm(user_prompt)
        print(f"Response:\n{result}")

    except Exception as e:
        print(f"Error: {e}")
