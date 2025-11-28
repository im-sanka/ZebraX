from unittest import result
import pytest
from pathlib import Path

def test_excel_to_json():
    from agents.zebra.data_template_handling import excel_to_json

    # Use relative path from the test file
    template_path = Path(__file__).parent.parent / "data" / "01" / "sample_template.xlsx"
    json_template = excel_to_json(str(template_path))
    expected_template = {
        "Title": "",
        "Venue Type": "",
        "Year": "",
        "URL": "",
        "Study type": "",
        "Testing Level": "",
        "Functional or non-functional?": "",
        "Non-functional requirement(s)": "",
        "Testing type": "",
        "Objective [SWEBOK]": "",
        "strategy (secification, )....[from SWEBOK]": ""
    }
    assert json_template == expected_template, f"Expected {expected_template}, but got {json_template}"
    
    
def test_keyword_seeker():
    from agents.zebra.data_template_handling import keyword_seeker
    
    sample_text = """In this paper, we propose an approach to observe and detect
performance degradation during the transition towards a microservice application. 
In the context of testing, our approach aims at avoiding performance regression during 
the transition from an old, monolithic, to a new microservice architecture.
In the context of Lean development, this approach can be seen as an implementation of 
Jidoka [8] (in English called Autonomation), which describes a mechanism, for which a 
machine is able to detect an anomaly by itself and then stop to allow workers to investigate
the reasons of the anomaly and restart the production. We see the contribution of our 
tool in the same way: if the new architecture performs under a given threshold, 
it might be time to stop developing and to rethink the architecture or to rethink 
the used patterns to guarantee that the new system—while having all advantages
of a microservice architecture—does not fall short in terms of performance"""
    keywords = "regression, microservice"
    
    results = keyword_seeker(sample_text, keywords)
    
    assert "regression" in results
    assert "microservice" in results
    
def test_table_filler():
    from agents.zebra.data_template_handling import data_template_filler
    
    json_template = {
        "regression": []
    }
    
    sample_text = """In this paper, we propose an approach to observe and detect
performance degradation during the transition towards a microservice application. 
In the context of testing, our approach aims at avoiding performance regression during 
the transition from an old, monolithic, to a new microservice architecture.
In the context of Lean development, this approach can be seen as an implementation of 
Jidoka [8] (in English called Autonomation), which describes a mechanism, for which a 
machine is able to detect an anomaly by itself and then stop to allow workers to investigate
the reasons of the anomaly and restart the production. We see the contribution of our 
tool in the same way: if the new architecture performs under a given threshold, 
it might be time to stop developing and to rethink the architecture or to rethink 
the used patterns to guarantee that the new system—while having all advantages
of a microservice architecture—does not fall short in terms of performance"""
    
    research_paper_title = "Automatic performance monitoring and regression testing during the transition from monolith to microservices"
    
    filled_template = data_template_filler(json_template, sample_text, research_paper_title)
    
    expected_filled_template = {
        "regression": ["Automatic performance monitoring and regression testing during the transition from monolith to microservices"]
    }
    
    assert filled_template == expected_filled_template, f"Expected {expected_filled_template}, but got {filled_template}"