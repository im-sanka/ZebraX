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
    filled_template = json_template.copy()
    for key in filled_template:
        if key.lower() in paper_text.lower():
            if isinstance(filled_template[key], list):
                filled_template[key].append(research_paper_title)
            else:
                filled_template[key] = research_paper_title
    return filled_template