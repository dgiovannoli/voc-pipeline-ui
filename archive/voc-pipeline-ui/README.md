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
