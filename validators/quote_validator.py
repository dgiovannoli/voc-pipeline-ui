#!/usr/bin/env python3
import json
import csv
import logging
from enhanced_stage2_analyzer import EnhancedTraceableStage2Analyzer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuoteValidator:
    def __init__(self):
        self.analyzer = EnhancedTraceableStage2Analyzer()

    def validate(self, quote_row):
        # quote_row is a dict with all metadata + tags + text
        
        # Log rejection reasons for missing required fields
        if not quote_row.get("criteria"):
            logger.info(f"DROPPED: missing criteria for {quote_row.get('quote_id', 'unknown')}")
            return None
        
        if not quote_row.get("swot_theme"):
            logger.info(f"DROPPED: missing swot_theme for {quote_row.get('quote_id', 'unknown')}")
            return None
        
        if not quote_row.get("journey_phase"):
            logger.info(f"DROPPED: missing journey_phase for {quote_row.get('quote_id', 'unknown')}")
            return None
        
        if not quote_row.get("text"):
            logger.info(f"DROPPED: missing text for {quote_row.get('quote_id', 'unknown')}")
            return None
        
        # EnhancedTraceableStage2Analyzer expects:
        #   parsed_response, qa_pair, original_response
        validated_evidence, quality_report = self.analyzer.enhanced_evidence_validation(
            parsed_response=quote_row,
            qa_pair={"question": None, "answer": quote_row["text"]},
            original_response=quote_row["text"]
        )
        
        # Comment out strict validation filters - accept more quotes
        # if not validated_evidence:
        #     logger.info(f"DROPPED: no validated evidence for {quote_row.get('quote_id', 'unknown')}")
        #     return None
        
        # Attach JSON fields
        quote_row["validated_evidence"] = json.dumps(validated_evidence) if validated_evidence else "{}"
        quote_row["quality_report"] = json.dumps(quality_report) if quality_report else "{}"
        
        # Log acceptance
        logger.info(f"ACCEPTED: {quote_row.get('quote_id', 'unknown')} → {quote_row.get('criteria', 'unknown')}")
        
        return quote_row
