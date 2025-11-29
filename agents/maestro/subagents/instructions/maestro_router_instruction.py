"""
Maestro Router Instruction

Instruction for the router that determines the current stage of the workflow.
"""

MAESTRO_ROUTER_INSTRUCTION = """Analyze the conversation context and determine what stage of the workflow we are in.

The Maestro workflow has THREE stages that MUST be followed sequentially:

## STAGE 1: research_questions
User needs help formulating research questions.
Indicators:
- User just started the conversation
- User mentions wanting to research something
- User asks for help with questions
- No research questions have been selected yet

## STAGE 2: article_analysis
User has selected research questions and needs to analyze articles.
Indicators:
- Research questions have been selected/confirmed
- User mentions having articles/PDFs
- User wants to search for articles
- User is ready to analyze

## STAGE 3: validation
Article analysis is complete and user wants to validate/summarize.
Indicators:
- Analysis results exist
- User mentions reference table
- User asks for summary
- User wants to compare results

## OUTPUT:
Output ONLY one of these words based on the current context:
- "research_questions" - Start with question formulation
- "article_analysis" - Proceed to article analysis
- "validation" - Perform validation and summary

Consider the session state:
- If "selected_questions" is empty → research_questions
- If "selected_questions" exists but "analysis_results" is empty → article_analysis
- If "analysis_results" exists → validation

Output ONLY the stage word, nothing else."""
