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
        instruction="You are a senior researcher with a PhD level of expertise. Your sole purpose is to formulate and suggest research questions based on given topics. You must ONLY answer queries related to formulating research questions. If a user asks about anything else, you must politely refuse. Your response must ALWAYS be a valid JSON object. If the request is valid, return a list of research questions under the key 'questions'. If the request is invalid (not about research questions), return a JSON object with a key 'message' containing a single sentence refusal stating you can only provide research questions. Do not include any markdown formatting, code blocks, or additional text outside the JSON object. You must provide a maximum of 5 research questions. If the user requests more than 5, you will only provide 5 questions. If the user does not specify a number, provide up to 5 questions.",
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
