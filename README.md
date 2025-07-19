# VoC Pipeline

A Voice of Customer (VoC) analysis pipeline for processing interview transcripts and extracting structured insights.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

The pipeline can be run directly from the command line using the `voc_pipeline` package:

```bash
python -m voc_pipeline process_transcript \
  samples/Buried_Wins_Leila_Vaez-Iravani.docx \
  Rev \
  "Law Offices of Leila Vaez-Iravani" \
  "Leila Vaez-Iravani" \
  "closed won" \
  "07/01/2025"
```

### Streamlit Web Interface

For a user-friendly web interface, run:

```bash
streamlit run app.py
```

## Features

- **Transcript Processing**: Supports both .docx and .txt files
- **Parallel Processing**: Handles multiple files simultaneously
- **Structured Output**: Generates comprehensive data tables with 20 insight columns
- **Web Interface**: User-friendly Streamlit app with metadata input
- **CLI Access**: Direct command-line processing for automation
- **Advanced Analytics**: Enhanced Stage 2 analysis with evidence integration
- **Report Generation**: Theme-driven story reports with scorecard framework

## Report Generation

### Theme-Story Scorecard Reports

Generate comprehensive Win/Loss reports where themes tell the story, evidence supports the narrative, and scorecard framework anchors the analysis:

```bash
python official_scripts/rev_theme_story_scorecard.py
```

**Key Features**:
- **Themes Drive Narrative**: Each criterion has compelling story themes
- **Evidence Matrix**: Findings and quotes support every theme
- **Scorecard Framework**: McKinsey-ready structure with weighted scoring
- **Strategic Insights**: Executive summary with competitive implications

### Enhanced Stage 2 Analysis

Advanced analysis with improved scoring methodology and evidence integration:

```bash
python official_scripts/enhanced_stage2_analyzer.py
```

## Project Structure

```
voc-pipeline-ui/
├── official_scripts/          # Production-ready scripts
│   ├── core_analytics/        # Analysis and processing scripts
│   ├── ui_components/         # Streamlit UI applications
│   ├── database/              # Database interaction modules
│   ├── utilities/             # Helper functions and utilities
│   └── rev_theme_story_scorecard.py  # Theme-driven story reports
├── drafts/                    # Development versions (git-ignored)
├── reports/                   # Generated reports (git-ignored)
├── voc_pipeline/             # Core pipeline modules
├── coders/                   # Response coding modules
├── validators/               # Quote validation
└── prompts/                  # Analysis prompts
```
