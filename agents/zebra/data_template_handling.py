import os
import pandas as pd
import re

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

def data_template_filler(json_template: dict, paper_text: str, research_paper_title: str) -> dict:
    """
    Fills the provided JSON template with data based on the research paper content.

    For each key in the json_template, if the key is found in the paper text, fill it with the research paper title.

    Args:
        json_template (dict): The JSON template with placeholders.
        paper_text (str): The extracted text content of the research paper.
        research_paper_title (str): The title of the research paper to fill into the template.
    """
    # filled_template = json_template.copy()
    # for key in filled_template:
    #     if key.lower() in paper_text.lower():
    #         filled_template[key] = research_paper_title
    # return filled_template
    pass

def keyword_seeker(paper_text: str, keywords: str) -> str:
    """
    Searches the research paper text for the provided keywords gathered from the JSON template.
    Keywords are from the JSON template keys.

    Args:
        paper_text (str): The extracted text content of the research paper.
        keywords (str): The keywords to search for in the research paper.
    """
    # Split keywords if comma-separated
    keyword_list = [kw.strip() for kw in keywords.split(',')]

    matches = []
    
    # Split text into sentences or paragraphs
    sentences = re.split(r'(?<=[.!?])\s+', paper_text)
    
    for sentence in sentences:
        if any(keyword.lower() in sentence.lower() for keyword in keyword_list):
            matches.append(sentence.strip())
    
    # If no relevant sections found, return a message
    if not matches:
        return "No keywords found."
    
    # Join relevant sections
    return "\n\n".join(matches)