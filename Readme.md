# ZebraX: Automated Systematic Review & Research Analysis Platform

ZebraX is an intelligent multi-agent system that automates systematic and scientific reviews using AI-powered research agents and Google's Agent Development Kit (ADK) for data extraction and processing.

## 🎯 Overview

ZebraX orchestrates three specialized AI agents to conduct comprehensive research reviews:

1. **Belo LLM** - Formulates research questions from data
2. **Zebra Agent** - Extracts and processes research data
3. **Cross Agent** - Validates results and performs statistical analysis

## 🏗️ Architecture

![ZebraX Architecture](./Architecture.png)

### System Components

#### 1. **Belo LLM** (Research Question Generator)
- **Purpose**: Simple agent that formulates research questions based on RAG (Retrieval-Augmented Generation) data
- **Model**: Google Gemini 2.5 Flash Lite (lightweight, fast inference)
- **Inputs**: 
  - User prompts
  - Sample articles (optional)
  - RAG pipeline with defined system prompts
- **Output**: Research questions to guide data extraction
- **Use Case**: When users don't have predefined research questions, Belo generates them from provided content
- **Why Gemini 2.5 Flash Lite**: Optimal for quick, lightweight processing without complex reasoning

#### 2. **Zebra Agent** (Multi-Agent Data Extractor)
- **Purpose**: Parallel and sequential data extraction from research materials
- **Root Agent Model**: Google Gemini 2.5 Pro (tool-native, optimized for function calling)
- **Sub-Agents**: Specialized Gemma 3 Multimodal instances for parallel processing
- **Components**:
  - **Root Agent**: Orchestrates and distributes tasks to Sub-Agents
  - **Sub-Agents**: Parallel workers with specialized extraction capabilities
  - **Data Extractor Tools** (native to Gemini):
    - Data parser (structured extraction)
    - Graph maker (relationship mapping)
    - Grammatical checker (text validation)
    - Additional domain-specific tools
- **Process**: 
  - Takes prompts and research questions as input
  - Root Agent receives research queries
  - Distributes extraction tasks to Sub-Agents in parallel
  - Sub-Agents leverage Gemini's native tool-calling capabilities
  - Optionally processes sample articles
  - Outputs structured results
- **Output**: Parsed data, graphs, validated content
- **Why Gemini 2.5 Pro & Gemma**: Native tool integration in Pro for coordination, while Gemma provides cost-effective multimodal processing for sub-tasks.

#### 3. **Cross Agent** (Statistical Validator & Judge)
- **Purpose**: Cross-validate results and perform statistical analysis
- **Model**: Google Gemini 2.5 Pro (advanced reasoning for complex data comparison)
- **Capabilities**:
  - Compares reference data with Zebra Agent results
  - Processes results directly when no reference is provided
  - Generates summary tables
  - Performs statistical validation
  - Outputs final article draft
  - Deep analysis and statistical reasoning
- **Output**: Validation results, statistical analysis, article summary
- **Why Gemini 2.5 Pro**: Superior reasoning capabilities for complex statistical analysis and cross-validation

### Data Flow

```
User Research Query
    ↓
    ├─→ [Belo LLM] → Research Questions
    ↓
Research Questions + Sample Articles
    ↓
    ├─→ [Zebra Agent] → Extracted Results
    ↓
Results + Reference Data (optional)
    ↓
    ├─→ [Cross Agent] → 
        ├─ Validation Result
        ├─ More Results
        └─ Article Draft
```

## 🔄 Workflow

![ZebraX Workflow](./Main-idea.png)

### Three-Checkpoint Systematic Review Process

1. **First Checkpoint: Ground Truth & Data Collection**
   - Establish research questions
   - Gather replication package data
   - Collect AI/perplexity research materials

2. **Second Checkpoint: Data Comparison**
   - Zebra Agent extracts and processes data
   - Compare extracted results with reference data
   - Prepare data for validation

3. **Third Checkpoint: Final Analysis**
   - Cross Agent validates findings
   - Performs statistical analysis
   - Generates article draft and comparison tables

## 🛠️ Technology Stack

### AI & LLM Components (Google AI)
- **Belo LLM**: Google Gemini 2.0 Flash (lightweight question generation)
- **Zebra Agent Root**: Google Gemini Pro 1.5 (tool orchestration & coordination)
- **Zebra Agent Sub-Agents**: Google Gemini Pro 1.5 (parallel data extraction with native tools)
- **Cross Agent**: Google Gemini 2.0 (advanced statistical analysis & reasoning)
- **Framework**: Google Agent Development Kit (ADK) (for agent orchestration, RAG pipeline, and multi-agent coordination)
- **Data Processing**: Python

### Data Extraction Tools (ADK Integration)
- **Agent Development Kit (ADK)**: For agent-level data extraction and processing
- **Data Parser**: Structured data extraction
- **Graph Maker**: Visual relationship mapping
- **Grammatical Checker**: Text validation

### Statistical Analysis
- **Python Libraries**: 
  - `pandas` for data manipulation
  - `scipy`/`statsmodels` for statistical tests
  - `matplotlib`/`seaborn` for visualization

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Google ADK installed and configured
- API keys for LLM services (OpenAI/Anthropic)
- Required Python dependencies

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ZebraX

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Set up environment variables:
```bash
export GOOGLE_API_KEY="your-google-ai-api-key"
export ADK_PATH="/path/to/agent-development-kit"
```

2. Configure RAG pipeline and system prompts

3. Set up reference data sources (optional)

### Running a Review

```bash
# Option 1: With research questions
python main.py --questions "research_questions.txt" --articles "sample_articles.txt"

# Option 2: Generate questions automatically
python main.py --belo --topic "Your research topic" --articles "sample_articles.txt"

# Option 3: Full workflow with validation
python main.py --full-review --reference "reference_data.json" --articles "materials.txt"
```

## 📊 Output

ZebraX generates:
- **Validation Results**: Cross-validation metrics
- **Summary Tables**: Structured data comparisons
- **Statistical Analysis**: p-values, effect sizes, confidence intervals
- **Article Draft**: AI-generated research summary
- **Extracted Data**: Structured graphs and parsed information

## 🔍 When to Use Each Component

| Scenario | Model | Use Case |
|----------|-------|----------|
| No research questions yet | Belo (Gemini 2.0 Flash) | Fast question generation |
| Need to extract data from articles | Zebra Agent (Gemini Pro 1.5 + Sub-Agents) | Parallel data extraction with tools |
| Need statistical validation | Cross Agent (Gemini 2.0) | Advanced analysis & comparison |
| Full systematic review | All three (in sequence) | Complete workflow |
| Just need AI research questions | Belo (Gemini 2.0 Flash) | Lightweight inference |

## ✅ Architecture Analysis

**Does this make sense? YES, with these considerations:**

### ✅ **Strengths:**
1. **Modular Design**: Each agent has a single, well-defined responsibility
2. **Scalability**: Zebra Agent's parallel processing allows efficient data extraction
3. **Flexibility**: Works with or without reference data
4. **Comprehensive**: Covers the full research review pipeline
5. **Validation Built-in**: Cross Agent ensures result quality

### 🤔 **Considerations:**
1. **Data Quality Dependency**: Results depend heavily on initial article quality and RAG pipeline effectiveness
2. **LLM Hallucination Risks**: Consider implementing fact-checking layers
3. **ADK Integration**: Ensure ADK tools are properly interfaced for your data types
4. **Error Handling**: Add fallback mechanisms when agents fail
5. **Cost**: Multiple LLM calls could be expensive—consider caching strategies

### 💡 **Suggested Improvements:**
1. Add a **validation feedback loop** - let Cross Agent inform Zebra Agent of extraction errors
2. Implement **confidence scores** - track certainty of extracted data
3. Add **human-in-the-loop** checkpoints for critical decisions
4. Create **audit trails** - log all agent decisions for reproducibility
5. Support **incremental reviews** - process large datasets in batches

## 👥 Authors

- [**im-sanka**](https://github.com/im-sanka)
- [**rahmanuh**](https://github.com/rahmanuh)

## 📞 Support

For issues and questions, please open an issue on GitHub.
