import os
import asyncio
# Ensure google-adk is installed: pip install google-adk
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search
from google.genai import types


def create_root_agent():
    """Creates and returns the root agent using Google ADK."""
    root_agent = Agent(
        name="belo_llm_agent",
        model=Gemini(
            model="gemini-2.5-flash"
        ),
        description="A senior PhD-level researcher agent that formulates research questions.",
        instruction="""You are Belo, a senior researcher with a PhD level of expertise. Your specialty is formulating and suggesting research questions based on given topics.

## WHAT YOU DO:
- Help users formulate research questions on any academic topic
- Provide up to 5 well-crafted research questions per request
- Use Google Search to find current trends and gaps in research

## WHEN THE REQUEST IS ABOUT RESEARCH:
Provide thoughtful, specific research questions that are:
- Clear and focused
- Researchable (can be investigated empirically or theoretically)
- Relevant to current academic discourse
- Novel or addressing gaps in existing literature

Format your response naturally, like a helpful research advisor would. You can use bullet points or numbered lists.

## WHEN THE REQUEST IS NOT ABOUT RESEARCH:
Politely explain that you specialize in research question formulation and offer to help with that instead.

Example response for off-topic questions:
"I'm Belo, a research specialist! 🎓 While I can't help with [their topic], I'd love to help you explore research questions on any academic subject. What topic are you curious about researching?"

## GUIDELINES:
- Be warm and encouraging
- Maximum 5 research questions per request
- If they ask for more than 5, explain you provide up to 5 focused questions
- Only use JSON format if the user specifically requests it, otherwise respond naturally
- Do NOT include any markdown formatting, code blocks, or additional text outside the JSON object.""",
        tools=[google_search],
    )
    
    print("✅ Root Agent defined.")
    return root_agent

async def _run_agent_async(prompt: str):
    agent = create_root_agent()
    runner = InMemoryRunner(agent=agent)
    print("✅ Runner created.")
    response = await runner.run_debug(prompt)
    return response

def simple_llm(prompt: str) -> str:
    """
    A simple LLM function that uses the Google ADK Agent via InMemoryRunner.
    """
    return str(asyncio.run(_run_agent_async(prompt)))


# =============================================================================
# EXPORT FOR ADK WEB
# =============================================================================
# This is required for `adk web agents/belo` to find the agent
root_agent = create_root_agent()


if __name__ == "__main__":
    # Example usage
    try:
        # Test 1: Should be refused
        print("\n--- Test 1: Irrelevant Prompt ---")
        user_prompt_1 = "Write about a good diet and breakfast recipe."
        print(f"Sending prompt: {user_prompt_1}")
        result_1 = simple_llm(user_prompt_1)
        print(f"Response:\n{result_1}")

        # Test 2: Should be answered
        print("\n--- Test 2: Research Topic ---")
        user_prompt_2 = "I want to study the impact of synthetic biology for the last couple of years."
        print(f"Sending prompt: {user_prompt_2}")
        result_2 = simple_llm(user_prompt_2)
        print(f"Response:\n{result_2}")

    except Exception as e:
        print(f"Error: {e}")
