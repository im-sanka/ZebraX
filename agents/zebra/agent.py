import os
import sys
import asyncio
from dotenv import load_dotenv
# Ensure google-adk is installed: pip install google-adk
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from agents.zebra.pdf_tool import read_pdf_text, extract_pdf_images, read_pdf_with_ocr, get_pdf_info, analyze_pdf_structure
from agents.zebra.data_template_handling import data_template_filler

load_dotenv()

def create_zebra_llm_agent():
    """Creates and returns the zebra_llm_agent using Google ADK and PDF tools."""
    zebra_agent = Agent(
        name="zebra_llm_agent",
        model=Gemini(
            model="gemini-2.5-flash"
        ),
        description="An intelligent agent capable of reading and analyzing PDF documents, including extracting text, images, and performing OCR.",
        instruction="""You are 'zebra_llm_agent', a specialized AI assistant for processing PDF documents.
        
        Your primary task is to analyze PDF documents and extract structured information.
        
        When asked to process a PDF, you must output a valid JSON object with the following structure:
        {
            "title": "The title of the document",
            "authors": ["List", "of", "authors"],
            "abstract": "The abstract text",
            "number_of_images": 0,
            "content_items": [
                {
                    "type": "image" or "table" or "data",
                    "page_number": 1,
                    "summary": "A brief summary or description of what this item depicts, inferred from context or caption."
                }
            ]
        }

        Tools available:
        - `read_pdf_text`: Use this to extract text for Title, Authors, Abstract, and to find captions/context for tables and images.
        - `extract_pdf_images`: Use this to count images and find their locations.
        - `get_pdf_info`: Use this to get metadata which might help with Title and Authors.
        - `data_template_filler`: Use this to fill in structured data templates.
        
        Process:
        1. Call `get_pdf_info` to get metadata.
        2. Call `read_pdf_text` to get the full text. Analyze the first few pages for Title, Authors, and Abstract.
        3. Call `extract_pdf_images` to get the list of images.
        4. Correlate images with the text on their pages to generate summaries (look for "Figure X", "Table Y" captions).
        5. Identify tables from the text layout if possible.
        6. Use `data_template_filler` to fill in structured data templates based on extracted information.
        
        Return ONLY the JSON object. Do not include markdown formatting like ```json.
        """,
        tools=[read_pdf_text, extract_pdf_images, read_pdf_with_ocr, get_pdf_info, analyze_pdf_structure, data_template_filler],
    )
    
    print("✅ Zebra LLM Agent defined.")
    return zebra_agent

async def _run_agent_async(prompt: str):
    agent = create_zebra_llm_agent()
    runner = InMemoryRunner(agent=agent)
    print("✅ Runner created.")
    response = await runner.run_debug(prompt)
    return response

def simple_llm(prompt: str) -> str:
    """
    A simple LLM function that uses the Zebra LLM Agent via InMemoryRunner.
    """
    return str(asyncio.run(_run_agent_async(prompt)))

if __name__ == "__main__":
    # Example usage
    try:
        if len(sys.argv) < 2:
            raise ValueError(f"Provide a file path to a PDF document. \nUsage: python {sys.argv[0]} /path/to/document.pdf")
        
        print("\n--- Test: PDF Agent ---")
        # You would need a sample PDF to test this effectively
        user_prompt = f"Read the text from this PDF: {sys.argv[1]}"
        print(f"Sending prompt: {user_prompt}")
        result = simple_llm(user_prompt)
        print(f"Response:\n{result}")
    except Exception as e:
        print(f"Error: {e}")
