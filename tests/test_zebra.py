import pytest

def test_excel_to_json():
    from agents.zebra.data_template_handling import excel_to_json

    json_template = excel_to_json("/Users/rhn07/src/ZebraX/data/01/sample_template.xlsx")
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