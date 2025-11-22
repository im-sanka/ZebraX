import os
import pandas as pd

def excel_to_json(file_path: str) -> dict:
    """
    Reads an Excel file and converts its header to a JSON dictionary keys.
    The keys will be passed to LLM for data filling.

    Args:
        file_path (str): The path to the Excel file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    df = pd.read_excel(file_path, nrows=0)  # Read only the header
    json_template = {col: "" for col in df.columns}
    return json_template

def data_template_filler(json_template: dict, research_paper_title: str, research_paper_link: str = None) -> dict:
    """
    Fills the provided JSON template with data based on the research paper content.

    TODO:
    - Calling domain_knowledge_retriever to get context-specific knowledge to help LLM fill the template.
    - Calling keyword semantic seeker to find relevant sections in the research paper.

    Args:
        json_template (dict): The JSON template with placeholders.
        research_paper_title (str): The title of the research paper to fill into the template.
        research_paper_link (str): The link of the research paper to fill into the template.
    """
    pass

def domain_knowledge_retriever(keywords: str) -> str:
    """
    Retrieves domain-specific knowledge to assist the LLM in understanding context.

    Args:
        keyword (str): The domain for which to retrieve knowledge.
    """
    pass

def keyword_semantic_seeker(research_paper_title: str, keywords: str) -> str:
    """
    Searches the research paper for sections relevant to the provided keywords.
    Keywords are from the JSON template keys.

    Args:
        research_paper_title (str): The title of the research paper.
        keywords (str): The keywords to search for in the research paper.
    """
    pass