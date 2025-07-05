# Archive Directory

This directory contains files that were moved during the codebase cleanup on July 5, 2025.

## What Was Archived

### Test Files
- `test_*.py` - Various test scripts that are no longer needed
- `test_*.csv` - Test output files from development
- `test_output.json` - Test JSON output
- `test_setup_quote.txt` - Test setup file

### Migration Scripts
- `migrate_*.py` - Old migration scripts for database setup
- `run_stage2.py` - Old Stage 2 runner script

### Backup Files
- `*.bak` - Backup files from development

### Old Data Files
- `stage1_*.csv` - Old Stage 1 output files
- `*quality.csv` - Quality assessment files
- `combined_test.csv` - Combined test data
- `response_data_table_*.csv` - Old response data files
- `passthrough_quotes.csv` - Old passthrough data
- `example_export.csv` - Example export file

### Development Files
- `database_examples.py` - Database usage examples
- `batch_passthrough.py` - Old batch processing script
- `requirements_stage2.txt` - Old requirements file
- `qc.log` - Quality control log file
- `.DS_Store` - macOS system file

### Duplicate Directory
- `voc-pipeline-ui/` - Nested duplicate of the main project directory

## Why These Files Were Archived

1. **No longer used** - These files are not imported or referenced by the main application
2. **Development artifacts** - Test files and outputs from the development process
3. **Outdated** - Files that have been superseded by newer implementations
4. **Duplicates** - Files that exist in multiple locations
5. **System files** - Files created by the operating system

## Current Active Files

The main application now consists of:
- `app.py` - Main Streamlit application
- `enhanced_stage2_analyzer.py` - Stage 2 analysis engine
- `database.py` - Database interface
- `config/` - Configuration files
- `prompts/` - AI prompt templates
- `voc_pipeline/` - Core pipeline modules
- `validators/`, `coders/`, `loaders/`, `ingestion/` - Supporting modules
- `voc_pipeline.db` - SQLite database
- `requirements.txt` - Current dependencies
- `pyproject.toml` - Project configuration

## Recovery

If you need to recover any of these files, they are safely stored in this archive directory. Simply move them back to the main directory if needed. 