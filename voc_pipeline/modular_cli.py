"""
Modular CLI Interface
Command-line interface for running individual pipeline stages or the full pipeline.
"""

import click
import json
import pandas as pd
from pathlib import Path
from typing import Optional
import logging

from .modular_processor import ModularProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Modular VOC Pipeline CLI - Run individual stages or full pipeline"""
    pass

@cli.command()
@click.argument('transcript_path')
@click.argument('company')
@click.argument('interviewee')
@click.argument('deal_status')
@click.argument('date_of_interview')
@click.option('--output', '-o', help='Output file for core responses (CSV or JSON)')
@click.option('--model', '-m', default='gpt-3.5-turbo-16k', help='LLM model to use')
def extract_core(transcript_path: str, company: str, interviewee: str, deal_status: str, 
                date_of_interview: str, output: Optional[str], model: str):
    """Stage 1: Extract core verbatim responses and metadata only."""
    try:
        processor = ModularProcessor(model_name=model)
        
        logger.info(f"Starting core extraction from {transcript_path}")
        responses = processor.stage1_core_extraction(
            transcript_path, company, interviewee, deal_status, date_of_interview
        )
        
        logger.info(f"Extracted {len(responses)} core responses")
        
        # Save to file if specified
        if output:
            if output.lower().endswith('.csv'):
                df = pd.DataFrame(responses)
                df.to_csv(output, index=False)
                logger.info(f"Saved core responses to {output} (CSV)")
            else:
                with open(output, 'w') as f:
                    json.dump(responses, f, indent=2)
                logger.info(f"Saved core responses to {output} (JSON)")
        
        # Print summary
        print(f"\n=== Core Extraction Results ===")
        print(f"Transcript: {transcript_path}")
        print(f"Company: {company}")
        print(f"Interviewee: {interviewee}")
        print(f"Responses extracted: {len(responses)}")
        
        if responses:
            print(f"\nSample response:")
            sample = responses[0]
            print(f"  ID: {sample.get('response_id', 'N/A')}")
            print(f"  Subject: {sample.get('subject', 'N/A')}")
            print(f"  Verbatim: {sample.get('verbatim_response', 'N/A')[:100]}...")
        
    except Exception as e:
        logger.error(f"Core extraction failed: {e}")
        raise

@cli.command()
@click.argument('stage1_data_responses_file')
@click.option('--output', '-o', help='Output JSON file for enriched responses')
@click.option('--model', '-m', default='gpt-3.5-turbo-16k', help='LLM model to use')
def enrich_analysis(stage1_data_responses_file: str, output: Optional[str], model: str):
    """Stage 2: Add AI-generated analysis to core responses."""
    try:
        processor = ModularProcessor(model_name=model)
        
        # Load core responses
        with open(stage1_data_responses_file, 'r') as f:
            stage1_data_responses = json.load(f)
        
        logger.info(f"Starting analysis enrichment for {len(stage1_data_responses)} responses")
        enriched_responses = processor.stage2_analysis_enrichment(stage1_data_responses)
        
        logger.info(f"Enriched {len(enriched_responses)} responses")
        
        # Save to file if specified
        if output:
            with open(output, 'w') as f:
                json.dump(enriched_responses, f, indent=2)
            logger.info(f"Saved enriched responses to {output}")
        
        # Print summary
        print(f"\n=== Analysis Enrichment Results ===")
        print(f"Input file: {stage1_data_responses_file}")
        print(f"Responses enriched: {len(enriched_responses)}")
        
        if enriched_responses:
            print(f"\nSample enriched response:")
            sample = enriched_responses[0]
            print(f"  ID: {sample.get('response_id', 'N/A')}")
            print(f"  Key Insight: {sample.get('key_insight', 'N/A')[:100]}...")
            print(f"  Findings: {sample.get('findings', 'N/A')[:100]}...")
        
    except Exception as e:
        logger.error(f"Analysis enrichment failed: {e}")
        raise

@cli.command()
@click.argument('responses_file')
@click.option('--output', '-o', help='Output JSON file for labeled responses')
@click.option('--model', '-m', default='gpt-3.5-turbo-16k', help='LLM model to use')
def add_labels(responses_file: str, output: Optional[str], model: str):
    """Stage 3: Add structured labels to responses."""
    try:
        processor = ModularProcessor(model_name=model)
        
        # Load responses
        with open(responses_file, 'r') as f:
            responses = json.load(f)
        
        logger.info(f"Starting labeling for {len(responses)} responses")
        labeled_responses = processor.stage3_labeling(responses)
        
        logger.info(f"Labeled {len(labeled_responses)} responses")
        
        # Save to file if specified
        if output:
            with open(output, 'w') as f:
                json.dump(labeled_responses, f, indent=2)
            logger.info(f"Saved labeled responses to {output}")
        
        # Print summary
        print(f"\n=== Labeling Results ===")
        print(f"Input file: {responses_file}")
        print(f"Responses labeled: {len(labeled_responses)}")
        
        if labeled_responses:
            print(f"\nSample labeled response:")
            sample = labeled_responses[0]
            print(f"  ID: {sample.get('response_id', 'N/A')}")
            labels = sample.get('labels', {})
            for label_type, label_data in labels.items():
                if isinstance(label_data, dict):
                    value = label_data.get('value', 'N/A')
                    confidence = label_data.get('confidence', 'N/A')
                    print(f"  {label_type}: {value} (confidence: {confidence})")
        
    except Exception as e:
        logger.error(f"Labeling failed: {e}")
        raise

@cli.command()
@click.argument('transcript_path')
@click.argument('company')
@click.argument('interviewee')
@click.argument('deal_status')
@click.argument('date_of_interview')
@click.option('--output', '-o', help='Output JSON file for complete results')
@click.option('--model', '-m', default='gpt-3.5-turbo-16k', help='LLM model to use')
@click.option('--save-db/--no-save-db', default=True, help='Save results to database')
def run_pipeline(transcript_path: str, company: str, interviewee: str, deal_status: str, 
                date_of_interview: str, output: Optional[str], model: str, save_db: bool):
    """Run the complete pipeline (all stages)."""
    try:
        processor = ModularProcessor(model_name=model)
        
        logger.info("Starting full pipeline")
        results = processor.run_full_pipeline(
            transcript_path, company, interviewee, deal_status, date_of_interview, save_db
        )
        
        # Save to file if specified
        if output:
            with open(output, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Saved complete results to {output}")
        
        # Print summary
        print(f"\n=== Full Pipeline Results ===")
        print(f"Transcript: {transcript_path}")
        print(f"Company: {company}")
        print(f"Interviewee: {interviewee}")
        print(f"Stage 1 (Core): {results['stage1_core_count']} responses")
        print(f"Stage 2 (Analysis): {results['stage2_enriched_count']} responses")
        print(f"Stage 3 (Labels): {results['stage3_labeled_count']} responses")
        print(f"Database saved: {results['database_saved_count']} responses")
        
        if results['responses']:
            print(f"\nSample complete response:")
            sample = results['responses'][0]
            print(f"  ID: {sample.get('response_id', 'N/A')}")
            print(f"  Subject: {sample.get('subject', 'N/A')}")
            print(f"  Key Insight: {sample.get('key_insight', 'N/A')[:100]}...")
            labels = sample.get('labels', {})
            if labels:
                print(f"  Labels: {len(labels)} label types")
        
    except Exception as e:
        logger.error(f"Full pipeline failed: {e}")
        raise

@cli.command()
@click.argument('responses_file')
@click.option('--output', '-o', help='Output CSV file')
def export_csv(responses_file: str, output: Optional[str]):
    """Export responses to CSV format."""
    try:
        # Load responses
        with open(responses_file, 'r') as f:
            responses = json.load(f)
        
        if not responses:
            logger.warning("No responses to export")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(responses)
        
        # Flatten labels if present
        if 'labels' in df.columns:
            # Extract label values
            for i, row in df.iterrows():
                labels = row.get('labels', {})
                if isinstance(labels, dict):
                    for label_type, label_data in labels.items():
                        if isinstance(label_data, dict):
                            df.at[i, f'label_{label_type}'] = label_data.get('value', '')
                            df.at[i, f'label_{label_type}_confidence'] = label_data.get('confidence', '')
            
            # Drop the original labels column
            df = df.drop('labels', axis=1, errors='ignore')
        
        # Save to CSV
        output_file = output or f"responses_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)
        
        logger.info(f"Exported {len(df)} responses to {output_file}")
        
        # Print summary
        print(f"\n=== CSV Export Results ===")
        print(f"Input file: {responses_file}")
        print(f"Output file: {output_file}")
        print(f"Responses exported: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print(f"Column names: {list(df.columns)}")
        
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise

if __name__ == "__main__":
    cli() 