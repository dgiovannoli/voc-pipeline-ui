#!/usr/bin/env python3
"""
Migration script to split existing wide CSV files into normalized database structure.

This script takes existing CSV files that contain both core fields and enrichment fields,
splits them into the proper normalized structure, and saves them to the database.

Usage:
    python migrate_csv_split.py --input stage1_output.csv --output core_output.csv --enrichment enrichment_output.csv
"""

import pandas as pd
import argparse
import sys
from pathlib import Path
from database import VOCDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def split_csv_data(input_path: str, core_output_path: str = None, enrichment_output_path: str = None, 
                   save_to_db: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split a wide CSV file into core and enrichment components.
    
    Args:
        input_path: Path to the input CSV file
        core_output_path: Path to save core fields CSV (optional)
        enrichment_output_path: Path to save enrichment fields CSV (optional)
        save_to_db: Whether to save the split data to the database
    
    Returns:
        Tuple of (core_df, enrichment_df)
    """
    
    # Read the input CSV
    logger.info(f"Reading CSV from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Read {len(df)} rows with columns: {list(df.columns)}")
    
    # Define core and enrichment field mappings
    core_fields = [
        'Response ID', 'Verbatim Response', 'Subject', 'Question', 
        'Deal Status', 'Company Name', 'Interviewee Name', 'Date of Interview'
    ]
    
    enrichment_fields = [
        'Key Insight', 'Findings', 'Value_Realization', 'Implementation_Experience',
        'Risk_Mitigation', 'Competitive_Advantage', 'Customer_Success', 
        'Product_Feedback', 'Service_Quality', 'Decision_Factors',
        'Pain_Points', 'Success_Metrics', 'Future_Plans'
    ]
    
    # Extract core fields
    core_df = df[core_fields].copy()
    logger.info(f"Extracted {len(core_df)} core records")
    
    # Extract enrichment fields
    enrichment_df = df[['Response ID'] + enrichment_fields].copy()
    logger.info(f"Extracted {len(enrichment_df)} enrichment records")
    
    # Save core fields to CSV if requested
    if core_output_path:
        core_df.to_csv(core_output_path, index=False)
        logger.info(f"Saved core fields to {core_output_path}")
    
    # Save enrichment fields to CSV if requested
    if enrichment_output_path:
        enrichment_df.to_csv(enrichment_output_path, index=False)
        logger.info(f"Saved enrichment fields to {enrichment_output_path}")
    
    # Save to database if requested
    if save_to_db:
        db = VOCDatabase()
        migrated_count = 0
        
        for _, row in df.iterrows():
            try:
                # Prepare core response data
                response_data = {
                    'response_id': row.get('Response ID', f"migrated_{migrated_count}"),
                    'verbatim_response': row.get('Verbatim Response', ''),
                    'subject': row.get('Subject', ''),
                    'question': row.get('Question', ''),
                    'deal_status': row.get('Deal Status', ''),
                    'company': row.get('Company Name', ''),
                    'interviewee_name': row.get('Interviewee Name', ''),
                    'date_of_interview': row.get('Date of Interview', ''),
                }
                
                # Add enrichment fields
                for field in enrichment_fields:
                    if field in row and pd.notna(row[field]) and row[field] != 'N/A':
                        response_data[field.lower().replace(' ', '_')] = row[field]
                
                # Save to database
                if db.save_response(response_data):
                    migrated_count += 1
                else:
                    logger.warning(f"Failed to save response {row.get('Response ID', migrated_count)}")
                    
            except Exception as e:
                logger.error(f"Error processing row {migrated_count}: {e}")
                continue
        
        logger.info(f"Successfully migrated {migrated_count} responses to database")
    
    return core_df, enrichment_df

def main():
    parser = argparse.ArgumentParser(description='Split wide CSV files into normalized structure')
    parser.add_argument('--input', '-i', required=True, help='Input CSV file path')
    parser.add_argument('--core-output', '-c', help='Output path for core fields CSV')
    parser.add_argument('--enrichment-output', '-e', help='Output path for enrichment fields CSV')
    parser.add_argument('--no-db', action='store_true', help='Skip saving to database')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    try:
        # Split the CSV data
        core_df, enrichment_df = split_csv_data(
            input_path=args.input,
            core_output_path=args.core_output,
            enrichment_output_path=args.enrichment_output,
            save_to_db=not args.no_db
        )
        
        # Print summary
        print(f"\n=== Migration Summary ===")
        print(f"Input file: {args.input}")
        print(f"Core records: {len(core_df)}")
        print(f"Enrichment records: {len(enrichment_df)}")
        
        if args.core_output:
            print(f"Core fields saved to: {args.core_output}")
        if args.enrichment_output:
            print(f"Enrichment fields saved to: {args.enrichment_output}")
        
        if not args.no_db:
            print("Data saved to database successfully")
        
        print(f"\nCore fields: {list(core_df.columns)}")
        print(f"Enrichment fields: {list(enrichment_df.columns)[1:]}")  # Skip Response ID
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 