#!/usr/bin/env python3
import json
import csv
from enhanced_stage2_analyzer import EnhancedTraceableStage2Analyzer

class QuoteValidator:
    def __init__(self):
        self.analyzer = EnhancedTraceableStage2Analyzer()

    def validate(self, quote_row):
        # quote_row is a dict with all metadata + tags + text
        # EnhancedTraceableStage2Analyzer expects:
        #   parsed_response, qa_pair, original_response
        validated_evidence, quality_report = self.analyzer.enhanced_evidence_validation(
            parsed_response=quote_row,
            qa_pair={"question": None, "answer": quote_row["text"]},
            original_response=quote_row["text"]
        )
        if not validated_evidence:
            return None
        # Attach JSON fields
        quote_row["validated_evidence"] = json.dumps(validated_evidence)
        quote_row["quality_report"] = json.dumps(quality_report)
        return quote_row
