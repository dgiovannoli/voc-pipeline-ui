# Modular Prompt System Guide

## Overview

The modular prompt system separates the VOC pipeline into three independent stages, allowing you to iterate on each stage without affecting the others. This provides maximum flexibility and control over your data processing workflow.

## Architecture

### Stage 1: Core Extraction
- **Purpose**: Extract clean verbatim responses and essential metadata
- **Output**: Core fields only (Response ID, Verbatim Response, Subject, Question, Deal Status, Company Name, Interviewee Name, Date of Interview)
- **Focus**: Quality verbatim extraction, proper metadata assignment
- **File**: `prompts/core_extraction.py`

### Stage 2: Analysis Enrichment
- **Purpose**: Generate AI insights from core verbatim responses
- **Input**: Core responses from Stage 1
- **Output**: Analysis results (Findings, Value Realization, Implementation Experience, etc.)
- **Focus**: Deep analysis, insights, recommendations
- **File**: `prompts/analysis_enrichment.py`

### Stage 3: Labeling
- **Purpose**: Add structured labels and classifications
- **Input**: Core responses + analysis results
- **Output**: Labels (sentiment, priority, actionable, topic, quality)
- **Focus**: Categorization, sentiment analysis, prioritization
- **File**: `prompts/labeling.py`

## Benefits

### 1. Independent Iteration
- Improve analysis prompts without affecting core data
- Test different labeling approaches on the same data
- Optimize each stage separately

### 2. Quality Control
- Validate each stage independently
- Identify issues at specific stages
- Maintain data integrity

### 3. Flexibility
- Run different analysis models on the same core data
- A/B test different approaches
- Skip stages when not needed

### 4. Versioning
- Track improvements in each stage separately
- Roll back changes to specific stages
- Maintain prompt history

### 5. Parallel Processing
- Run analysis and labeling in parallel
- Process different batches with different approaches
- Scale individual stages

## Usage Examples

### Command Line Interface

#### Run Individual Stages

```bash
# Stage 1: Extract core responses only
python -m voc_pipeline.modular_cli extract-core transcript.txt "TechCorp" "John Doe" "closed_won" "2024-01-01" -o core_responses.json

# Stage 2: Add analysis to core responses
python -m voc_pipeline.modular_cli enrich-analysis core_responses.json -o enriched_responses.json

# Stage 3: Add labels to responses
python -m voc_pipeline.modular_cli add-labels enriched_responses.json -o labeled_responses.json
```

#### Run Full Pipeline

```bash
# Run all stages at once
python -m voc_pipeline.modular_cli run-pipeline transcript.txt "TechCorp" "John Doe" "closed_won" "2024-01-01" -o complete_results.json
```

#### Export to CSV

```bash
# Export results to CSV
python -m voc_pipeline.modular_cli export-csv labeled_responses.json -o final_export.csv
```

### Python API

```python
from voc_pipeline.modular_processor import ModularProcessor

# Initialize processor
processor = ModularProcessor(model_name="gpt-3.5-turbo-16k")

# Stage 1: Core extraction
core_responses = processor.stage1_core_extraction(
    "transcript.txt", "TechCorp", "John Doe", "closed_won", "2024-01-01"
)

# Stage 2: Analysis enrichment
enriched_responses = processor.stage2_analysis_enrichment(core_responses)

# Stage 3: Labeling
labeled_responses = processor.stage3_labeling(enriched_responses)

# Save to database
saved_count = processor.save_to_database(labeled_responses)
```

## Workflow Scenarios

### Scenario 1: Iterative Improvement
1. Run Stage 1 to get core responses
2. Review and validate core data quality
3. Iterate on Stage 2 analysis prompts
4. Test different analysis approaches
5. Finalize with Stage 3 labeling

### Scenario 2: A/B Testing
1. Extract core responses once
2. Run different analysis models on the same core data
3. Compare results and choose the best approach
4. Apply consistent labeling

### Scenario 3: Quality Control
1. Run Stage 1 and validate core data
2. Run Stage 2 and review analysis quality
3. Run Stage 3 and check label accuracy
4. Fix issues at specific stages

### Scenario 4: Parallel Processing
1. Extract core responses
2. Run analysis and labeling in parallel
3. Combine results
4. Save to database

## Prompt Customization

### Modifying Core Extraction
Edit `prompts/core_extraction.py`:
- Adjust verbatim response rules
- Modify subject categories
- Change extraction strategy

### Modifying Analysis
Edit `prompts/analysis_enrichment.py`:
- Add new analysis dimensions
- Modify analysis approach
- Adjust insight extraction

### Modifying Labeling
Edit `prompts/labeling.py`:
- Add new label types
- Modify label categories
- Adjust confidence scoring

## Best Practices

### 1. Start with Core Extraction
- Focus on quality verbatim responses
- Ensure accurate metadata
- Validate core data before proceeding

### 2. Iterate on Analysis
- Test different analysis approaches
- Validate insights quality
- Compare results across models

### 3. Validate Labels
- Check label consistency
- Review confidence scores
- Ensure proper categorization

### 4. Version Control
- Track prompt changes
- Document improvements
- Maintain prompt history

### 5. Quality Assurance
- Validate each stage independently
- Check data integrity
- Monitor performance metrics

## File Structure

```
prompts/
├── __init__.py              # Package initialization
├── core_extraction.py       # Stage 1: Core extraction prompt
├── analysis_enrichment.py   # Stage 2: Analysis enrichment prompt
└── labeling.py             # Stage 3: Labeling prompt

voc_pipeline/
├── modular_processor.py    # Main processor class
└── modular_cli.py         # Command line interface
```

## Integration with Existing System

The modular system is designed to work alongside the existing pipeline:

- **Backward Compatible**: Existing pipeline continues to work
- **Database Integration**: Uses the same normalized database structure
- **Streamlit UI**: Can be integrated into the existing UI
- **Migration Tools**: Existing migration tools work with modular output

## Next Steps

1. **Test the modular system** with your existing data
2. **Iterate on prompts** based on your specific needs
3. **Integrate into Streamlit UI** for easier management
4. **Add more stages** as needed (e.g., quality scoring, summarization)
5. **Implement A/B testing** for prompt optimization

This modular approach gives you the flexibility to continuously improve each stage of your VOC pipeline while maintaining data integrity and quality. 