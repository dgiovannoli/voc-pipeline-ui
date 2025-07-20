#!/usr/bin/env python3

import os
import json
import re
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
import concurrent.futures
import hashlib
from datetime import datetime
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import time
import threading

load_dotenv()

# Thread-safe progress tracking for Stage 2
stage2_progress_lock = threading.Lock()
stage2_progress_data = {"completed_batches": 0, "total_batches": 0, "results": [], "errors": []}

class EnhancedTraceableStage2Analyzer:
    def __init__(self):
        self.llm = OpenAI(
            model_name="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=16000,
            temperature=0.1
        )
        
        self.criteria = {
            # Core Solution Factors
            "product_capability": "Functionality, performance, solution fit, feature completeness, technical capabilities",
            "implementation_onboarding": "Deployment ease, time-to-value, setup complexity, training requirements, go-live process",
            "integration_technical_fit": "APIs, compatibility, architecture alignment, data integration, technical requirements",
            
            # Trust & Risk Factors
            "support_service_quality": "Post-sale experience, responsiveness, expertise, SLAs, customer success",
            "security_compliance": "Data protection, governance, risk management, certifications, compliance standards",
            "market_position_reputation": "Brand trust, references, analyst recognition, market presence, thought leadership",
            "vendor_stability": "Financial health, roadmap clarity, long-term viability, company stability, growth trajectory",
            
            # Experience & Commercial Factors
            "sales_experience_partnership": "Buying process quality, relationship building, trust, partnership approach",
            "commercial_terms": "Price, contract flexibility, ROI, total cost of ownership, payment terms",
            "speed_responsiveness": "Implementation timeline, decision-making agility, response times, project velocity"
        }
        
        # Quality tracking
        self.quality_metrics = {
            "total_quotes": 0,
            "high_quality_quotes": 0,
            "rejected_quotes": 0,
            "quality_issues": {}
        }
    
    def validate_quote_quality(self, evidence_entry, qa_pair, original_response):
        """Enhanced validation layer for quote quality"""
        
        quote = evidence_entry.get("supporting_quote", "")
        context = evidence_entry.get("quote_context", "")
        subject_verification = evidence_entry.get("subject_verification", "")
        speaker_verification = evidence_entry.get("speaker_verification", "")
        relevance_explanation = evidence_entry.get("relevance_explanation", "")
        
        quality_issues = []
        
        # Check quote length and context
        quote_words = len(quote.split())
        if quote_words < 8:
            quality_issues.append("Quote too short, lacks context")
        elif quote_words > 50:
            quality_issues.append("Quote too long, may include multiple topics")
        
        # Check for ambiguous pronouns without clear antecedents
        ambiguous_pronouns = ["they", "it", "them", "their", "this", "that"]
        quote_lower = quote.lower()
        pronoun_found = any(pronoun in quote_lower for pronoun in ambiguous_pronouns)
        
        if pronoun_found:
            # Check if Rev or service is clearly referenced
            rev_references = ["rev", "service", "transcription", "company", "vendor", "solution"]
            if not any(ref in quote_lower for ref in rev_references):
                quality_issues.append("Ambiguous subject reference - unclear if about Rev")
        
        # Check for numerical values without sufficient context
        import re
        price_matches = re.findall(r'\$\d+|\d+%|\d+\s*dollars?|\d+\s*cents?', quote)
        if price_matches and quote_words < 12:
            quality_issues.append("Numerical reference lacks sufficient context")
        
        # Check for interviewer language patterns
        interviewer_patterns = [
            r'\bdo you\b', r'\bwhat about\b', r'\bhow did\b', r'\bcan you tell me\b',
            r'\bwould you say\b', r'\bin your opinion\b', r'\bwhat do you think\b',
            r'\bhave you\b', r'\bdid you\b', r'\bwould you\b', r'\bcould you\b'
        ]
        
        if any(re.search(pattern, quote_lower) for pattern in interviewer_patterns):
            quality_issues.append("Contains interviewer question patterns")
        
        # Check for question marks (likely interviewer)
        if '?' in quote:
            quality_issues.append("Contains question mark - likely interviewer quote")
        
        # Verify verification fields are meaningful
        if not subject_verification or len(subject_verification.strip()) < 10:
            quality_issues.append("Subject verification insufficient")
        
        if not speaker_verification or len(speaker_verification.strip()) < 10:
            quality_issues.append("Speaker verification insufficient")
        
        if not relevance_explanation or len(relevance_explanation.strip()) < 10:
            quality_issues.append("Relevance explanation insufficient")
        
        # Check for competitor mentions
        competitor_names = [
            "otter", "trint", "descript", "speechmatics", "assembly", "deepgram",
            "transcribe", "sonix", "happy scribe", "temi", "fireflies"
        ]
        
        if any(comp in quote_lower for comp in competitor_names):
            # Check if it's comparing to Rev or just about competitor
            if "rev" not in quote_lower and "compared to" not in quote_lower:
                quality_issues.append("Quote appears to be about competitor, not Rev")
        
        # Check for generic/vague statements
        generic_patterns = [
            r'^it (is|was) (good|bad|okay|fine)\.?$',
            r'^(good|bad|okay|fine)\.?$',
            r'^(yes|no)\.?$',
            r'^i (like|love|hate|dislike) (it|them)\.?$'
        ]
        
        if any(re.match(pattern, quote_lower.strip()) for pattern in generic_patterns):
            quality_issues.append("Quote too generic/vague")
        
        return quality_issues
    
    def calculate_quality_score(self, quality_issues):
        """Calculate quality score based on issues found"""
        max_score = 100
        deductions = {
            "Quote too short, lacks context": 30,
            "Quote too long, may include multiple topics": 20,
            "Ambiguous subject reference - unclear if about Rev": 40,
            "Numerical reference lacks sufficient context": 25,
            "Contains interviewer question patterns": 50,
            "Contains question mark - likely interviewer quote": 60,
            "Subject verification insufficient": 25,
            "Speaker verification insufficient": 25,
            "Relevance explanation insufficient": 20,
            "Quote appears to be about competitor, not Rev": 45,
            "Quote too generic/vague": 35
        }
        
        quality_score = max_score
        for issue in quality_issues:
            if issue in deductions:
                quality_score -= deductions[issue]
        
        return max(0, quality_score)
    
    def enhanced_evidence_validation(self, parsed_response, qa_pair, original_response):
        """Enhanced validation with quality scoring"""
        
        validated_evidence = {}
        quality_report = {}
        
        evidence = parsed_response.get("evidence", {})
        
        for criterion, evidence_entry in evidence.items():
            quality_issues = self.validate_quote_quality(evidence_entry, qa_pair, original_response)
            quality_score = self.calculate_quality_score(quality_issues)
            
            # Track quality metrics
            self.quality_metrics["total_quotes"] += 1
            
            # Only include high-quality evidence (60% threshold)
            if quality_score >= 60:
                validated_evidence[criterion] = evidence_entry.copy()
                validated_evidence[criterion]["quality_score"] = quality_score
                validated_evidence[criterion]["quality_issues"] = quality_issues
                self.quality_metrics["high_quality_quotes"] += 1
            else:
                self.quality_metrics["rejected_quotes"] += 1
            
            # Track quality issues
            for issue in quality_issues:
                self.quality_metrics["quality_issues"][issue] = self.quality_metrics["quality_issues"].get(issue, 0) + 1
            
            quality_report[criterion] = {
                "quality_score": quality_score,
                "issues": quality_issues,
                "included": quality_score >= 60
            }
        
        return validated_evidence, quality_report
    
    def fix_json_response(self, response_text):
        """Robust JSON fixing that handles common LLM JSON errors"""
        try:
            # First try to parse as-is
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Extract JSON from response if it's embedded in other text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            return None
            
        json_text = json_match.group(0)
        
        # Common fixes for malformed JSON
        fixes_applied = []
        
        # Fix 1: Remove trailing commas before } or ]
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        fixes_applied.append("trailing_commas")
        
        # Fix 2: Add missing commas between object properties
        json_text = re.sub(r'"\s*\n\s*"', '",\n"', json_text)
        
        # Fix 3: Fix unquoted keys
        json_text = re.sub(r'(\w+):', r'"\1":', json_text)
        
        # Fix 4: Remove extra data after JSON object
        # Find the last closing brace and cut there
        last_brace = json_text.rfind('}')
        if last_brace != -1:
            json_text = json_text[:last_brace + 1]
        
        # Fix 5: Handle missing quotes around string values
        json_text = re.sub(r':\s*([^",{\[\]}\s][^",{\[\]}\n]*)', r': "\1"', json_text)
        
        # Try parsing after each fix
        for attempt in range(3):
            try:
                return json.loads(json_text)
            except json.JSONDecodeError as e:
                if attempt == 0:
                    # Fix missing commas between properties (more aggressive)
                    json_text = re.sub(r'"\s+(["{])', r'", \1', json_text)
                elif attempt == 1:
                    # Fix incomplete objects by adding closing braces
                    open_braces = json_text.count('{')
                    close_braces = json_text.count('}')
                    if open_braces > close_braces:
                        json_text += '}' * (open_braces - close_braces)
                else:
                    # Last resort: try to extract just the scores section
                    scores_match = re.search(r'"scores":\s*\{[^}]*\}', json_text)
                    if scores_match:
                        return {"scores": json.loads(scores_match.group(0).split(':', 1)[1])}
        
        return None
    
    def parse_response_with_fallback(self, response_text):
        """Parse LLM response with multiple fallback strategies"""
        
        # Strategy 1: Fix JSON and parse normally
        parsed = self.fix_json_response(response_text)
        if parsed:
            return parsed
        
        # Strategy 2: Extract information using regex patterns
        fallback_result = {
            "scores": {},
            "evidence": {},
            "priorities": {},
            "competitors": [],
            "confidence": {}
        }
        
        # Extract scores using multiple regex patterns
        score_patterns = [
            r'"(\w+)":\s*(-?\d+\.?\d*)',
            r'(\w+):\s*(-?\d+\.?\d*)',
            r'"scores"[^}]*"(\w+)":\s*(-?\d+\.?\d*)',
            r'(\w+)["\s]*:\s*["\s]*(-?\d+\.?\d*)',
            r'"(\w+)"\s*[-:]\s*(-?\d+\.?\d*)'
        ]
        
        for pattern in score_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for criterion, score in matches:
                if criterion.lower().replace('_', '') in [c.lower().replace('_', '') for c in self.criteria.keys()]:
                    # Find the exact criterion name
                    exact_criterion = None
                    for c in self.criteria.keys():
                        if c.lower().replace('_', '') == criterion.lower().replace('_', ''):
                            exact_criterion = c
                            break
                    
                    if exact_criterion:
                        try:
                            score_val = float(score)
                            if -5 <= score_val <= 5:
                                fallback_result["scores"][exact_criterion] = score_val
                        except ValueError:
                            continue
        
        # Extract evidence quotes using multiple patterns
        quote_patterns = [
            r'"supporting_quote":\s*"([^"]{15,200})"',
            r'supporting_quote[^"]*"([^"]{15,200})"',
            r'"quote":\s*"([^"]{15,200})"',
            r'"evidence"[^"]*"([^"]{15,200})"'
        ]
        
        quotes_found = []
        for pattern in quote_patterns:
            quotes_found.extend(re.findall(pattern, response_text, re.IGNORECASE))
        
        # Filter and validate quotes
        quality_quotes = []
        for quote in quotes_found:
            quote = quote.strip()
            # Basic quality check
            if (len(quote.split()) >= 8 and
                quote not in quality_quotes and
                not quote.lower().startswith('criterion') and
                not quote.lower().startswith('score') and
                '?' not in quote):  # Exclude likely interviewer questions
                quality_quotes.append(quote)
        
        # Match quotes to scored criteria
        for i, (criterion, score) in enumerate(fallback_result["scores"].items()):
            if i < len(quality_quotes):
                fallback_result["evidence"][criterion] = {
                    "supporting_quote": quality_quotes[i][:300],
                    "quote_context": "extracted via enhanced fallback parsing",
                    "subject_verification": "fallback extraction - subject unclear",
                    "speaker_verification": "fallback extraction - speaker unclear",
                    "relevance_explanation": "extracted through pattern matching",
                    "quote_strength": "weak",
                    "sentiment_direction": "positive" if score > 0 else "negative" if score < 0 else "neutral"
                }
        
        return fallback_result if fallback_result["scores"] else None
    
    def generate_quote_id(self, file_name, qa_id, criterion):
        """Generate unique identifier for each quote to enable traceability"""
        unique_string = f"{file_name}_{qa_id}_{criterion}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def detect_file_deal_outcome(self, file_name):
        file_lower = file_name.lower()
        
        if any(term in file_lower for term in ['won', 'win', 'success', 'closed_won']):
            return "won"
        elif any(term in file_lower for term in ['lost', 'loss', 'lose', 'closed_lost']):
            return "lost"
        else:
            return "unknown"
    
    def extract_customer_id(self, file_name):
        """Extract customer identifier from filename for traceability"""
        customer_id = file_name.replace('.json', '').replace('.txt', '').replace('.docx', '')
        return customer_id
    
    def analyze_single_qa_enhanced(self, qa_pair, deal_outcome, file_name):
        prompt = PromptTemplate(
            input_variables=["question", "response", "criteria", "deal_outcome"],
            template="""
            CRITICAL: You are analyzing CUSTOMER responses only. Do NOT include interviewer questions or statements.
            
            Analyze this Q&A for Rev transcription service feedback ONLY.
            
            DEAL CONTEXT: This is from a {deal_outcome} deal.
            
            EVALUATION CRITERIA:
            {criteria}
            
            CUSTOMER FEEDBACK:
            Q: {question}
            A: {response}
            
            EVIDENCE EXTRACTION RULES:
            
            1. SPEAKER VERIFICATION:
               - ONLY extract quotes from the CUSTOMER/INTERVIEWEE responses
               - NEVER include interviewer questions or statements
               - If unclear who is speaking, do NOT include the quote
            
            2. SUBJECT VERIFICATION:
               - ONLY include quotes that clearly reference Rev or "the service"
               - If they mention competitors by name, exclude those quotes
               - If subject is ambiguous (just "they" or "it"), include surrounding context
            
            3. CONTEXT REQUIREMENTS:
               - Extract 15-40 words including context before/after the key phrase
               - Include enough context to understand what they're discussing
               - For numerical references (prices), include the context explaining what the number refers to
            
            4. RELEVANCE VERIFICATION:
               - Quote must clearly support the criterion being scored
               - Explain HOW the quote relates to the criterion
               - If connection is unclear, do not score
            
            ENHANCED JSON FORMAT:
            {{
                "scores": {{
                    "criterion_name": score_number
                }},
                "evidence": {{
                    "criterion_name": {{
                        "supporting_quote": "Extended quote with sufficient context (15-40 words)",
                        "quote_context": "Clear explanation of what they're discussing and why it supports this criterion",
                        "subject_verification": "Confirmed this is about Rev/the service (not competitor)",
                        "speaker_verification": "Confirmed this is customer/interviewee speaking (not interviewer)",
                        "relevance_explanation": "Specific explanation of how this quote supports the criterion score",
                        "quote_strength": "strong|moderate|weak",
                        "sentiment_direction": "positive|negative|neutral"
                    }}
                }},
                "priorities": {{
                    "criterion_name": "critical|high|medium|low"
                }},
                "competitors": [],
                "confidence": {{
                    "criterion_name": "high|medium|low"
                }}
            }}
            
            EXAMPLES OF GOOD vs BAD QUOTES:
            
            BAD: "$150 a month" (no context)
            GOOD: "Rev charges $150 a month for their premium transcription package, which I think is reasonable for what we get"
            
            BAD: "it just was not as accurate" (unclear subject)
            GOOD: "Rev's transcription was not as accurate as I expected, especially with technical legal terms"
            
            BAD: "They weren't very good" (unclear who "they" refers to)
            GOOD: "Rev's transcripts weren't very good, with missed words and poor speaker identification"
            
            DISQUALIFY QUOTES IF:
            - Speaker is unclear (could be interviewer)
            - Subject is unclear (could be about competitor)
            - Context is insufficient to understand meaning
            - Relevance to criterion is unclear
            - Quote is just a number/price without explanation
            - Quote contains question marks (likely interviewer)
            
            CRITICAL RULES:
            - Use exact criterion names from the provided list
            - Only score criteria with supporting evidence
            - Use double quotes for all strings
            - No trailing commas
            - No text outside the JSON object
            """
        )
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({
                "question": qa_pair["question"][:400],
                "response": qa_pair["response"][:800],
                "criteria": '\n'.join([f"- {k}: {v}" for k, v in self.criteria.items()]),
                "deal_outcome": deal_outcome
            })
            
            # Use improved JSON parsing
            parsed = self.parse_response_with_fallback(result)
            
            if parsed:
                # Apply enhanced quality validation
                validated_evidence, quality_report = self.enhanced_evidence_validation(
                    parsed, qa_pair, result
                )
                
                # Update parsed response with validated evidence
                parsed["evidence"] = validated_evidence
                
                # Remove scores for criteria without quality evidence
                validated_scores = {}
                for criterion, score in parsed.get("scores", {}).items():
                    if criterion in validated_evidence:
                        validated_scores[criterion] = score
                parsed["scores"] = validated_scores
                
                if validated_scores:  # Only proceed if we have quality evidence
                    validated = self.validate_and_enhance_analysis(parsed, qa_pair, deal_outcome, file_name)
                    validated["quality_report"] = quality_report
                    return validated
                else:
                    return self.create_empty_analysis(qa_pair, deal_outcome, file_name, "No quality evidence found")
            else:
                print(f"JSON parsing failed completely for QA {qa_pair.get('qa_id', 'unknown')}")
                return self.create_empty_analysis(qa_pair, deal_outcome, file_name, "JSON parsing failed")
            
        except Exception as e:
            print(f"Analysis error for QA {qa_pair.get('qa_id', 'unknown')}: {e}")
            return self.create_empty_analysis(qa_pair, deal_outcome, file_name, str(e))
    
    def validate_and_enhance_analysis(self, parsed, qa_pair, deal_outcome, file_name):
        """Validate AI output and add traceability metadata"""
        validated = {
            "qa_id": qa_pair["qa_id"],
            "deal_outcome": deal_outcome,
            "file_source": file_name,
            "customer_id": self.extract_customer_id(file_name),
            "question_context": qa_pair["question"][:200],
            "response_preview": qa_pair["response"][:200],
            "analysis_timestamp": datetime.now().isoformat(),
            "scores": {},
            "evidence_trail": {},
            "priorities": {},
            "competitors": [],
            "confidence": {}
        }
        
        # Validate scores and create evidence trail
        scores = parsed.get("scores", {})
        evidence = parsed.get("evidence", {})
        
        for criterion, score in scores.items():
            if (criterion in self.criteria and
                isinstance(score, (int, float)) and
                -5 <= score <= 5):
                
                # Only include score if there's supporting evidence
                if criterion in evidence and evidence[criterion].get("supporting_quote"):
                    validated["scores"][criterion] = score
                    
                    # Create detailed evidence trail entry
                    quote_id = self.generate_quote_id(file_name, qa_pair["qa_id"], criterion)
                    
                    evidence_entry = evidence[criterion]
                    validated["evidence_trail"][criterion] = {
                        "quote_id": quote_id,
                        "supporting_quote": evidence_entry.get("supporting_quote", "")[:300],
                        "quote_context": evidence_entry.get("quote_context", ""),
                        "subject_verification": evidence_entry.get("subject_verification", ""),
                        "speaker_verification": evidence_entry.get("speaker_verification", ""),
                        "relevance_explanation": evidence_entry.get("relevance_explanation", ""),
                        "quote_strength": evidence_entry.get("quote_strength", "moderate"),
                        "sentiment_direction": evidence_entry.get("sentiment_direction", "neutral"),
                        "quality_score": evidence_entry.get("quality_score", 0),
                        "quality_issues": evidence_entry.get("quality_issues", []),
                        "score_contribution": score,
                        "original_question": qa_pair["question"],
                        "full_response_available": True
                    }
        
        # Validate priorities (only for scored criteria)
        priorities = parsed.get("priorities", {})
        valid_priority_levels = ["critical", "high", "medium", "low"]
        for criterion, priority in priorities.items():
            if (criterion in validated["scores"] and
                isinstance(priority, str) and
                priority.lower() in valid_priority_levels):
                validated["priorities"][criterion] = priority.lower()
        
        # Validate and enhance competitor mentions
        competitors = parsed.get("competitors", [])
        validated_competitors = []
        if isinstance(competitors, list):
            for comp in competitors:
                if isinstance(comp, dict):
                    validated_competitors.append({
                        "competitor_name": str(comp.get("competitor_name", "")).strip(),
                        "context": str(comp.get("context", ""))[:150],
                        "comparison_type": comp.get("comparison_type", "neutral"),
                        "mentioned_in_qa": qa_pair["qa_id"]
                    })
                elif isinstance(comp, str) and comp.strip():
                    validated_competitors.append({
                        "competitor_name": str(comp).strip(),
                        "context": "mentioned in response",
                        "comparison_type": "neutral",
                        "mentioned_in_qa": qa_pair["qa_id"]
                    })
        validated["competitors"] = validated_competitors
        
        # Validate confidence (only for scored criteria)
        confidence = parsed.get("confidence", {})
        valid_confidence_levels = ["high", "medium", "low"]
        for criterion, conf_level in confidence.items():
            if (criterion in validated["scores"] and
                isinstance(conf_level, str) and
                conf_level.lower() in valid_confidence_levels):
                validated["confidence"][criterion] = conf_level.lower()
        
        return validated
    
    def create_empty_analysis(self, qa_pair, deal_outcome, file_name, error=None):
        """Create empty analysis structure for failed analyses"""
        result = {
            "qa_id": qa_pair["qa_id"],
            "deal_outcome": deal_outcome,
            "file_source": file_name,
            "customer_id": self.extract_customer_id(file_name),
            "question_context": qa_pair["question"][:200],
            "response_preview": qa_pair["response"][:200],
            "analysis_timestamp": datetime.now().isoformat(),
            "scores": {},
            "evidence_trail": {},
            "priorities": {},
            "competitors": [],
            "confidence": {}
        }
        if error:
            result["error"] = error
        return result
    
    def generate_quality_metrics_report(self):
        """Generate quality metrics report"""
        total = self.quality_metrics["total_quotes"]
        high_quality = self.quality_metrics["high_quality_quotes"]
        rejected = self.quality_metrics["rejected_quotes"]
        
        if total == 0:
            return
        
        quality_percentage = (high_quality / total * 100) if total > 0 else 0
        
        print(f"\n📊 QUOTE QUALITY METRICS:")
        print(f"   Total quotes extracted: {total}")
        print(f"   High-quality quotes: {high_quality} ({quality_percentage:.1f}%)")
        print(f"   Rejected due to quality issues: {rejected} ({100-quality_percentage:.1f}%)")
        
        if self.quality_metrics["quality_issues"]:
            print(f"\n⚠️  COMMON QUALITY ISSUES:")
            sorted_issues = sorted(self.quality_metrics["quality_issues"].items(),
                                 key=lambda x: x[1], reverse=True)
            for issue, count in sorted_issues[:5]:  # Top 5 issues
                percentage = (count / total * 100)
                print(f"   • {issue}: {count} quotes ({percentage:.1f}%)")
    
    def apply_deal_outcome_weighting(self, score, deal_outcome):
        """Apply deal outcome weighting with detailed rationale"""
        if deal_outcome == "unknown":
            return {
                "weighted_score": score,
                "weight_factor": 1.0,
                "weighting_logic": "no_deal_outcome_data",
                "rationale": "No deal outcome information available for weighting"
            }
        
        if deal_outcome == "lost":
            if score < 0:
                weight_factor = 1.3
                logic = "negative_feedback_lost_deal_higher_weight"
                rationale = "Negative feedback in lost deal likely contributed to loss"
            else:
                weight_factor = 0.7
                logic = "positive_feedback_lost_deal_lower_weight"
                rationale = "Positive feedback in lost deal was insufficient to win"
        
        elif deal_outcome == "won":
            if score < 0:
                weight_factor = 0.7
                logic = "negative_feedback_won_deal_lower_weight"
                rationale = "Negative feedback in won deal was overcome by other factors"
            else:
                weight_factor = 1.3
                logic = "positive_feedback_won_deal_higher_weight"
                rationale = "Positive feedback in won deal likely contributed to win"
        
        weighted_score = score * weight_factor
        weighted_score = max(-5, min(5, weighted_score))
        
        return {
            "weighted_score": round(weighted_score, 1),
            "weight_factor": weight_factor,
            "weighting_logic": logic,
            "rationale": rationale
        }
    
    def create_criteria_evidence_summary(self, analyses, criterion):
        """Create comprehensive evidence summary for a criterion across all Q&A pairs"""
        evidence_summary = {
            "criterion": criterion,
            "total_mentions": 0,
            "evidence_entries": [],
            "score_distribution": {},
            "confidence_levels": {},
            "priority_levels": {},
            "quote_strength_distribution": {},
            "quality_metrics": {
                "average_quality_score": 0,
                "high_quality_count": 0,
                "quality_issues_summary": {}
            }
        }
        
        quality_scores = []
        
        for analysis in analyses:
            if criterion in analysis.get("evidence_trail", {}):
                evidence_entry = analysis["evidence_trail"][criterion]
                score = analysis["scores"][criterion]
                
                # Track quality metrics
                quality_score = evidence_entry.get("quality_score", 0)
                quality_scores.append(quality_score)
                
                if quality_score >= 80:
                    evidence_summary["quality_metrics"]["high_quality_count"] += 1
                
                # Track quality issues
                for issue in evidence_entry.get("quality_issues", []):
                    evidence_summary["quality_metrics"]["quality_issues_summary"][issue] = \
                        evidence_summary["quality_metrics"]["quality_issues_summary"].get(issue, 0) + 1
                
                # Add detailed evidence entry
                evidence_summary["evidence_entries"].append({
                    "quote_id": evidence_entry["quote_id"],
                    "customer_id": analysis["customer_id"],
                    "qa_id": analysis["qa_id"],
                    "supporting_quote": evidence_entry["supporting_quote"],
                    "score_contribution": score,
                    "quote_strength": evidence_entry["quote_strength"],
                    "sentiment_direction": evidence_entry["sentiment_direction"],
                    "quality_score": quality_score,
                    "subject_verification": evidence_entry.get("subject_verification", ""),
                    "speaker_verification": evidence_entry.get("speaker_verification", ""),
                    "relevance_explanation": evidence_entry.get("relevance_explanation", ""),
                    "confidence": analysis.get("confidence", {}).get(criterion, "unknown"),
                    "priority": analysis.get("priorities", {}).get(criterion, "unknown"),
                    "deal_outcome": analysis["deal_outcome"],
                    "question_context": evidence_entry["original_question"][:100]
                })
                
                evidence_summary["total_mentions"] += 1
                
                # Track distributions
                evidence_summary["score_distribution"][score] = evidence_summary["score_distribution"].get(score, 0) + 1
                
                conf = analysis.get("confidence", {}).get(criterion, "unknown")
                evidence_summary["confidence_levels"][conf] = evidence_summary["confidence_levels"].get(conf, 0) + 1
                
                prio = analysis.get("priorities", {}).get(criterion, "unknown")
                evidence_summary["priority_levels"][prio] = evidence_summary["priority_levels"].get(prio, 0) + 1
                
                strength = evidence_entry["quote_strength"]
                evidence_summary["quote_strength_distribution"][strength] = evidence_summary["quote_strength_distribution"].get(strength, 0) + 1
        
        # Calculate average quality score
        if quality_scores:
            evidence_summary["quality_metrics"]["average_quality_score"] = round(sum(quality_scores) / len(quality_scores), 1)
        
        return evidence_summary
    
    def process_file_enhanced(self, file_result):
        file_name = file_result["file"]
        qa_pairs = file_result["qa_pairs"]
        deal_outcome = self.detect_file_deal_outcome(file_name)
        
        print(f"\n📋 {file_name}")
        print(f"   🎯 Deal Outcome: {deal_outcome.upper()}")
        print(f"   Analyzing {len(qa_pairs)} Q&A pairs with enhanced quality controls...")
        
        analyses = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_qa = {
                executor.submit(self.analyze_single_qa_enhanced, qa, deal_outcome, file_name): qa["qa_id"]
                for qa in qa_pairs
            }
            
            successful = 0
            total_scores = 0
            criteria_hit = set()
            all_competitors = []
            total_evidence_entries = 0
            
            for future in concurrent.futures.as_completed(future_to_qa):
                try:
                    analysis = future.result()
                    analyses.append(analysis)
                    
                    score_count = len(analysis.get("scores", {}))
                    evidence_count = len(analysis.get("evidence_trail", {}))
                    
                    if score_count > 0:
                        successful += 1
                        total_scores += score_count
                        total_evidence_entries += evidence_count
                        criteria_hit.update(analysis["scores"].keys())
                        all_competitors.extend(analysis.get("competitors", []))
                        
                except Exception as e:
                    print(f"   ❌ Error processing Q&A: {e}")
                    pass
        
        print(f"   ✅ {successful}/{len(qa_pairs)} Q&A pairs with quality scores")
        print(f"   🎯 {total_scores} total criteria scores with {total_evidence_entries} evidence entries")
        print(f"   📋 {len(criteria_hit)} criteria covered")
        print(f"   🏢 {len(all_competitors)} competitor mentions")
        
        # Create comprehensive criteria analysis with evidence trails
        criteria_analysis = {}
        
        for criterion in criteria_hit:
            evidence_summary = self.create_criteria_evidence_summary(analyses, criterion)
            
            raw_scores = [entry["score_contribution"] for entry in evidence_summary["evidence_entries"]]
            
            if raw_scores:
                weighted_scores = []
                for analysis in analyses:
                    if criterion in analysis.get("scores", {}):
                        raw_score = analysis["scores"][criterion]
                        weighting_result = self.apply_deal_outcome_weighting(raw_score, analysis["deal_outcome"])
                        weighted_scores.append(weighting_result["weighted_score"])
                
                criteria_analysis[criterion] = {
                    "performance_metrics": {
                        "raw_average": round(sum(raw_scores) / len(raw_scores), 1),
                        "weighted_average": round(sum(weighted_scores) / len(weighted_scores), 1),
                        "mention_count": len(raw_scores),
                        "score_range": [min(raw_scores), max(raw_scores)]
                    },
                    "evidence_summary": evidence_summary,
                    "traceability": {
                        "total_evidence_entries": len(evidence_summary["evidence_entries"]),
                        "quote_ids": [entry["quote_id"] for entry in evidence_summary["evidence_entries"]],
                        "customer_sources": list(set(entry["customer_id"] for entry in evidence_summary["evidence_entries"]))
                    }
                }
        
        return {
            "file": file_name,
            "customer_id": self.extract_customer_id(file_name),
            "deal_outcome": deal_outcome,
            "criteria_analysis": criteria_analysis,
            "competitors_mentioned": all_competitors,
            "qa_with_scores": successful,
            "total_scores": total_scores,
            "total_evidence_entries": total_evidence_entries,
            "criteria_coverage": len(criteria_hit),
            "detailed_analyses": analyses
        }

def run_enhanced_traceability_analysis():
    analyzer = EnhancedTraceableStage2Analyzer()
    
    try:
        with open('improved_results.json', 'r') as f:
            stage1_data = json.load(f)
    except FileNotFoundError:
        print("❌ improved_results.json not found!")
        return
    
    print("🚀 ENHANCED STAGE 2: FULL TRACEABILITY + QUALITY CONTROLS")
    print("=" * 60)
    print("📊 Analyzing against ALL 10 criteria with complete evidence tracking")
    print("🔍 NEW QUALITY CONTROL FEATURES:")
    print("  • Enhanced speaker verification (customer vs interviewer)")
    print("  • Subject verification (Rev vs competitor mentions)")
    print("  • Context sufficiency validation (15-40 word quotes)")
    print("  • Relevance explanation requirements")
    print("  • Quality scoring with 60% minimum threshold")
    print("  • Comprehensive quality metrics reporting")
    print()
    
    file_results = [r for r in stage1_data["results"] if r.get("qa_pairs")]
    
    final_results = []
    all_criteria_found = set()
    all_competitors = []
    deal_outcomes = {}
    total_evidence_entries = 0
    
    for file_result in file_results:
        result = analyzer.process_file_enhanced(file_result)
        final_results.append(result)
        all_criteria_found.update(result['criteria_analysis'].keys())
        all_competitors.extend(result['competitors_mentioned'])
        total_evidence_entries += result['total_evidence_entries']
        
        outcome = result['deal_outcome']
        deal_outcomes[outcome] = deal_outcomes.get(outcome, 0) + 1
    
    # Generate quality metrics report
    analyzer.generate_quality_metrics_report()
    
    # Create overall performance with complete evidence trails
    overall_performance = {}
    
    for criterion in all_criteria_found:
        all_evidence_entries = []
        raw_scores = []
        weighted_scores = []
        
        for result in final_results:
            if criterion in result['criteria_analysis']:
                analysis = result['criteria_analysis'][criterion]
                evidence_summary = analysis['evidence_summary']
                
                all_evidence_entries.extend(evidence_summary['evidence_entries'])
                
                for entry in evidence_summary['evidence_entries']:
                    raw_scores.append(entry['score_contribution'])
                    
                    # Apply weighting
                    weighting_result = analyzer.apply_deal_outcome_weighting(
                        entry['score_contribution'],
                        entry['deal_outcome']
                    )
                    weighted_scores.append(weighting_result['weighted_score'])
        
        if raw_scores:
            # Calculate quality metrics for this criterion
            quality_scores = [entry.get('quality_score', 0) for entry in all_evidence_entries]
            avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0
            high_quality_count = len([q for q in quality_scores if q >= 80])
            
            overall_performance[criterion] = {
                "performance_metrics": {
                    "raw_average": round(sum(raw_scores) / len(raw_scores), 1),
                    "weighted_average": round(sum(weighted_scores) / len(weighted_scores), 1),
                    "total_mentions": len(raw_scores),
                    "score_range": [min(raw_scores), max(raw_scores)]
                },
                "evidence_traceability": {
                    "total_evidence_entries": len(all_evidence_entries),
                    "unique_customers": len(set(entry['customer_id'] for entry in all_evidence_entries)),
                    "evidence_quality": {
                        "average_quality_score": avg_quality,
                        "high_quality_count": high_quality_count,
                        "high_confidence": len([e for e in all_evidence_entries if e['confidence'] == 'high']),
                        "strong_quotes": len([e for e in all_evidence_entries if e['quote_strength'] == 'strong']),
                        "critical_priority": len([e for e in all_evidence_entries if e['priority'] == 'critical'])
                    },
                    "sample_evidence": all_evidence_entries[:3]  # Top 3 evidence entries for preview
                },
                "complete_evidence_trail": all_evidence_entries  # Full evidence for Stage 4
            }
    
    output = {
        "enhanced_results": final_results,
        "overall_performance": overall_performance,
        "competitive_landscape": {
            "all_competitors_mentioned": all_competitors,
            "competitor_count": len(set(comp['competitor_name'] for comp in all_competitors))
        },
        "deal_outcome_distribution": deal_outcomes,
        "quality_metrics": analyzer.quality_metrics,
        "traceability_metrics": {
            "total_evidence_entries": total_evidence_entries,
            "evidence_per_criterion": {
                criterion: len(perf["complete_evidence_trail"])
                for criterion, perf in overall_performance.items()
            },
            "evidence_quality_distribution": {
                "total_high_confidence": sum(
                    perf["evidence_traceability"]["evidence_quality"]["high_confidence"]
                    for perf in overall_performance.values()
                ),
                "total_strong_quotes": sum(
                    perf["evidence_traceability"]["evidence_quality"]["strong_quotes"]
                    for perf in overall_performance.values()
                ),
                "average_quality_score": round(sum(
                    perf["evidence_traceability"]["evidence_quality"]["average_quality_score"]
                    for perf in overall_performance.values()
                ) / len(overall_performance), 1) if overall_performance else 0
            }
        },
        "summary": {
            "total_qa_analyzed": sum(r["qa_with_scores"] for r in final_results),
            "total_criteria_scores": sum(r["total_scores"] for r in final_results),
            "criteria_with_data": f"{len(overall_performance)}/10",
            "missing_criteria": [c for c in analyzer.criteria.keys() if c not in overall_performance],
            "files_analyzed": len(final_results)
        }
    }
    
    with open("enhanced_stage2_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n🎉 ENHANCED QUALITY-CONTROLLED ANALYSIS COMPLETE!")
    print(f"📊 {output['summary']['total_qa_analyzed']} Q&A pairs analyzed")
    print(f"🔍 {total_evidence_entries} evidence entries created with quality validation")
    print(f"📋 {len(overall_performance)}/10 criteria have performance data")
    print(f"🏢 {len(set(comp['competitor_name'] for comp in all_competitors))} unique competitors")
    
    print(f"\n📈 PERFORMANCE SCORECARD WITH ENHANCED QUALITY:")
    print("=" * 85)
    print(f"{'Criterion':<35} {'Score':<6} {'Evidence':<8} {'Quality':<10} {'Issues':<15}")
    print("-" * 85)
    
    sorted_criteria = sorted(overall_performance.items(), key=lambda x: x[1]["performance_metrics"]["weighted_average"])
    
    for criterion, perf in sorted_criteria:
        score = perf["performance_metrics"]["weighted_average"]
        evidence_count = perf["evidence_traceability"]["total_evidence_entries"]
        avg_quality = perf["evidence_traceability"]["evidence_quality"]["average_quality_score"]
        high_quality = perf["evidence_traceability"]["evidence_quality"]["high_quality_count"]
        
        quality_display = f"{avg_quality:.0f}% ({high_quality}HQ)"
        
        print(f"{criterion:<35} {score:+5.1f}  {evidence_count:<7} {quality_display:<10}")
    
    print(f"\n🔍 ENHANCED EVIDENCE QUALITY SUMMARY:")
    print(f"   📊 {total_evidence_entries} total evidence entries with quality validation")
    print(f"   ✅ {output['quality_metrics']['high_quality_quotes']} high-quality quotes ({(output['quality_metrics']['high_quality_quotes']/max(output['quality_metrics']['total_quotes'],1)*100):.1f}%)")
    print(f"   ❌ {output['quality_metrics']['rejected_quotes']} quotes rejected due to quality issues")
    print(f"   📈 Average quality score: {output['traceability_metrics']['evidence_quality_distribution']['average_quality_score']:.1f}%")
    
    print(f"\n💡 STAGE 4 READINESS:")
    print(f"   ✅ High-quality evidence chains ready for synthesis")
    print(f"   ✅ Quote IDs enable full traceability to executive summary")
    print(f"   ✅ Quality metrics support reliable consensus building")
    print(f"   ✅ Enhanced validation reduces false positives")

# Run the enhanced analysis
if __name__ == "__main__":
    run_enhanced_traceability_analysis()

class SupabaseStage2Analyzer:
    """Supabase-integrated Stage 2 analyzer with parallel batched processing"""
    
    def __init__(self, batch_size=50, max_workers=4):  # Optimized parallel processing
        self.batch_size = batch_size
        self.max_workers = max_workers  # Increased from 2 to 4 for better performance
        self.supabase = None
        try:
            from supabase_database import SupabaseDatabase
            self.supabase = SupabaseDatabase()
        except ImportError:
            print("Warning: Supabase database not available")
    
    def process_incremental(self, client_id="default"):
        """Process quotes from database for Stage 2 analysis with parallel batch processing"""
        if not self.supabase:
            raise Exception("Supabase database not available")
        
        # Get quotes from database
        quotes_df = self.supabase.get_stage1_data_responses(client_id=client_id)
        if quotes_df.empty:
            print("No quotes found for analysis")
            return {"success": False, "message": "No quotes found"}
        
        print(f"Processing {len(quotes_df)} quotes in batches of {self.batch_size} with {self.max_workers} workers...")
        
        # Reset progress data
        global stage2_progress_data
        with stage2_progress_lock:
            stage2_progress_data = {
                "completed_batches": 0,
                "total_batches": (len(quotes_df) + self.batch_size - 1) // self.batch_size,
                "results": [],
                "errors": []
            }
        
        # Create batches
        batches = []
        for i in range(0, len(quotes_df), self.batch_size):
            batch = quotes_df.iloc[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            batches.append((batch_num, batch, client_id))
        
        # Process batches in parallel
        total_processed = 0
        total_analyzed = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batch processing tasks
            future_to_batch = {
                executor.submit(self._process_batch_parallel, batch_info): batch_info 
                for batch_info in batches
            }
            
            # Monitor progress and collect results
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_info = future_to_batch[future]
                batch_num = batch_info[0]
                
                try:
                    batch_result = future.result()
                    total_processed += batch_result.get('batch_size', 0)
                    total_analyzed += batch_result.get('analyzed_count', 0)
                    
                    print(f"✅ Batch {batch_num} completed: {batch_result.get('analyzed_count', 0)}/{batch_result.get('batch_size', 0)} quotes analyzed")
                    
                except Exception as e:
                    print(f"❌ Error processing batch {batch_num}: {e}")
                    with stage2_progress_lock:
                        stage2_progress_data["errors"].append({
                            'batch_num': batch_num,
                            'error': str(e)
                        })
                    continue
        
        print(f"\n🎉 Stage 2 analysis completed!")
        print(f"📊 Total quotes processed: {total_processed}")
        print(f"📊 Total quotes analyzed: {total_analyzed}")
        if total_processed > 0:
            print(f"📈 Success rate: {(total_analyzed/total_processed*100):.1f}%")
        else:
            print(f"📈 Success rate: 0.0% (no quotes processed)")
        
        return {
            "success": True,
            "processed_quotes": total_processed,
            "analyzed_quotes": total_analyzed,
            "success_rate": total_analyzed/total_processed if total_processed > 0 else 0
        }

    def _process_batch_parallel(self, batch_info: tuple) -> Dict:
        """Process a batch of quotes through the LLM (thread-safe version)"""
        batch_num, batch_df, client_id = batch_info
        
        try:
            # Reduced delay to speed up processing
            time.sleep(0.1)  # Reduced from 0.5 to 0.1 seconds
            
            # Prepare batch data for LLM
            batch_text = self._prepare_batch_for_llm(batch_df)

            # Call LLM with batch
            llm_response = self._call_llm_batch(batch_text)
            results = self._parse_llm_batch_response(llm_response, batch_df)

            # Save results to database
            self._save_batch_results_to_database(results, client_id)

            # Update progress
            with stage2_progress_lock:
                stage2_progress_data["completed_batches"] += 1
                stage2_progress_data["results"].append({
                    'batch_num': batch_num,
                    'analyzed_count': len(results),
                    'batch_size': len(batch_df)
                })

            return {
                "analyzed_count": len(results),
                "batch_size": len(batch_df)
            }

        except Exception as e:
            print(f"Error in batch {batch_num} processing: {e}")
            with stage2_progress_lock:
                stage2_progress_data["errors"].append({
                    'batch_num': batch_num,
                    'error': str(e)
                })
            return {"analyzed_count": 0, "batch_size": len(batch_df)}

    def _process_batch(self, batch_df, client_id):
        """Legacy sequential batch processing - kept for fallback"""
        # Prepare batch data for LLM
        batch_text = self._prepare_batch_for_llm(batch_df)

        # Call LLM with batch
        try:
            llm_response = self._call_llm_batch(batch_text)
            # FIX: Parse the LLM response into structured results
            results = self._parse_llm_batch_response(llm_response, batch_df)

            # Save results to database
            self._save_batch_results_to_database(results, client_id)

            return {
                "analyzed_count": len(results),
                "batch_size": len(batch_df)
            }

        except Exception as e:
            print(f"Error in batch processing: {e}")
            return {"analyzed_count": 0, "batch_size": len(batch_df)}

    def _prepare_batch_for_llm(self, batch_df):
        """Helper to prepare batch text for LLM, including headers and criteria"""
        batch_text = """Analyze the following customer quotes for relevance to 10 executive criteria. For each quote, provide a JSON response with:

1. Relevance scores (0-5) for each criterion where 0=not mentioned, 1=slight mention, 2=clear mention, 3=strong emphasis, 4=critical feedback, 5=exceptional praise
2. Sentiment (positive/negative/neutral/mixed)
3. Priority level (critical/high/medium/low)
4. Confidence level (high/medium/low)
5. Brief explanation of relevance

The 10 executive criteria are:
1. product_capability: Functionality, features, performance, core solution fit
2. implementation_onboarding: Deployment ease, time-to-value, setup complexity
3. integration_technical_fit: APIs, data compatibility, technical architecture
4. support_service_quality: Post-sale support, responsiveness, expertise, SLAs
5. security_compliance: Data protection, certifications, governance, risk management
6. market_position_reputation: Brand trust, references, analyst recognition
7. vendor_stability: Financial health, roadmap clarity, long-term viability
8. sales_experience_partnership: Buying process quality, relationship building
9. commercial_terms: Price, contract flexibility, ROI, total cost of ownership
10. speed_responsiveness: Implementation timeline, decision-making speed, agility

Respond with a JSON array where each element has: quote_id, relevance_scores (object with criterion names as keys), sentiment, priority, confidence, explanation.

Quotes:\n"""
        
        for idx, row in batch_df.iterrows():
            quote_id = row['response_id'] if 'response_id' in row else f'quote_{idx}'
            quote_text = row['verbatim_response'] if 'verbatim_response' in row else ''
            customer_name = row['interviewee_name'] if 'interviewee_name' in row else 'Unknown'
            deal_status = row['deal_status'] if 'deal_status' in row else 'Unknown'
            
            # Truncate long quotes to improve processing speed
            if len(quote_text) > 1000:
                quote_text = quote_text[:1000] + "... [truncated]"
            
            batch_text += f"Quote ID: {quote_id}\n"
            batch_text += f"Customer: {customer_name}\n"
            batch_text += f"Deal Status: {deal_status}\n"
            batch_text += f"Text: {quote_text}\n\n"
        
        return batch_text
    
    def _call_llm_batch(self, batch_text):
        """Call LLM with batched quotes - Enhanced version with better parsing and sentiment analysis"""
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate
        
        llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=3000,  # Increased for better response quality
            temperature=0.1
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert competitive intelligence analyst specializing in B2B SaaS customer feedback analysis. Your task is to analyze customer quotes and map them to executive criteria with precise sentiment analysis.

CRITICAL INSTRUCTIONS:
- Respond with ONLY valid JSON array. No additional text, explanations, or markdown.
- Each quote must be analyzed against ALL 10 criteria, not just top 1-3.
- Provide detailed sentiment analysis for each criterion mentioned.
- Use specific sentiment indicators to determine positive/negative/neutral/mixed.

SENTIMENT ANALYSIS FRAMEWORK:
POSITIVE INDICATORS: love, excellent, amazing, solved, improved, saved, great, perfect, outstanding, exceeded, delighted, satisfied, works perfectly, highly recommend, game-changer, efficient, fast, reliable, user-friendly, intuitive

NEGATIVE INDICATORS: hate, terrible, broken, failed, frustrated, problem, awful, disappointing, waste, slow, unreliable, difficult, confusing, expensive, overpriced, buggy, crashes, doesn't work, poor quality, terrible support

MIXED INDICATORS: but, however, although, despite, even though, on the other hand, while, yet, nevertheless, still, though

NEUTRAL INDICATORS: factual statements, descriptions, process explanations, feature lists, technical specifications

RELEVANCE SCORING (0-5):
- 0: Not mentioned at all
- 1: Slight mention, passing reference
- 2: Clear mention, some detail
- 3: Strong emphasis, detailed discussion
- 4: Critical feedback, major focus
- 5: Exceptional emphasis, central to the conversation

CRITERIA IDENTIFICATION EXAMPLES:
- "accuracy", "quality", "features", "functionality" → product_capability
- "setup", "implementation", "onboarding", "deployment" → implementation_onboarding
- "integration", "API", "technical", "compatibility" → integration_technical_fit
- "support", "help", "service", "response" → support_service_quality
- "security", "compliance", "data protection" → security_compliance
- "reputation", "brand", "trust", "references" → market_position_reputation
- "stability", "vendor", "company", "long-term" → vendor_stability
- "sales", "buying", "relationship", "partnership" → sales_experience_partnership
- "price", "cost", "pricing", "ROI", "expensive" → commercial_terms
- "speed", "fast", "quick", "time", "efficiency" → speed_responsiveness

SENTIMENT ASSIGNMENT RULES:
- Analyze each criterion independently for sentiment
- Look for specific sentiment words and phrases
- Consider context and tone of the feedback
- A high relevance score (4-5) with positive sentiment = strong positive feedback
- A high relevance score (4-5) with negative sentiment = strong negative feedback
- Mixed sentiment when quote contains both positive and negative elements about the same criterion

THE 10 EXECUTIVE CRITERIA:
1. product_capability: Functionality, features, performance, core solution fit, accuracy, quality
2. implementation_onboarding: Deployment ease, time-to-value, setup complexity, training
3. integration_technical_fit: APIs, data compatibility, technical architecture, integration
4. support_service_quality: Post-sale support, responsiveness, expertise, SLAs, customer service
5. security_compliance: Data protection, certifications, governance, risk management, security
6. market_position_reputation: Brand trust, references, analyst recognition, reputation
7. vendor_stability: Financial health, roadmap clarity, long-term viability, company stability
8. sales_experience_partnership: Buying process quality, relationship building
9. commercial_terms: Price, contract flexibility, ROI, total cost of ownership, pricing
10. speed_responsiveness: Implementation timeline, decision-making speed, agility, efficiency

OUTPUT FORMAT (JSON array only):
[
  {{
    "quote_id": "string",
    "relevance_scores": {{
      "product_capability": 0-5,
      "implementation_onboarding": 0-5,
      "integration_technical_fit": 0-5,
      "support_service_quality": 0-5,
      "security_compliance": 0-5,
      "market_position_reputation": 0-5,
      "vendor_stability": 0-5,
      "sales_experience_partnership": 0-5,
      "commercial_terms": 0-5,
      "speed_responsiveness": 0-5
    }},
    "criterion_sentiments": {{
      "product_capability": "positive|negative|neutral|mixed",
      "implementation_onboarding": "positive|negative|neutral|mixed",
      "integration_technical_fit": "positive|negative|neutral|mixed",
      "support_service_quality": "positive|negative|neutral|mixed",
      "security_compliance": "positive|negative|neutral|mixed",
      "market_position_reputation": "positive|negative|neutral|mixed",
      "vendor_stability": "positive|negative|neutral|mixed",
      "sales_experience_partnership": "positive|negative|neutral|mixed",
      "commercial_terms": "positive|negative|neutral|mixed",
      "speed_responsiveness": "positive|negative|neutral|mixed"
    }},
    "overall_sentiment": "positive|negative|neutral|mixed",
    "primary_criterion": "criterion_name",
    "secondary_criterion": "criterion_name|null",
    "tertiary_criterion": "criterion_name|null",
    "priority": "critical|high|medium|low",
    "confidence": "high|medium|low",
    "explanation": "brief explanation of analysis"
  }}
]

IMPORTANT: Only include criteria with relevance scores > 0 in criterion_sentiments. For criteria with relevance score 0, omit from criterion_sentiments."""),
            ("user", batch_text)
        ])
        
        response = llm.invoke(prompt.format_messages())
        return response.content
    
    def _parse_llm_batch_response(self, llm_response, batch_df):
        """Parse LLM response for batch of quotes - Enhanced version with multi-criteria support"""
        results = []
        
        try:
            # Clean the response and extract JSON
            cleaned_response = self._clean_llm_response(llm_response)
            
            # Try to parse as JSON array
            try:
                parsed_results = json.loads(cleaned_response)
                if not isinstance(parsed_results, list):
                    parsed_results = [parsed_results]
            except json.JSONDecodeError:
                # Try to extract JSON array using regex
                import re
                json_match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_results = json.loads(json_str)
                else:
                    raise Exception("No valid JSON array found in response")
            
            # Process each result
            for result in parsed_results:
                if isinstance(result, dict) and 'quote_id' in result:
                    # Normalize and validate the result
                    normalized_result = self._normalize_enhanced_result_fields(result)
                    if normalized_result:
                        results.append(normalized_result)
                else:
                    print(f"Warning: Invalid result format: {result}")
            
            # If no valid results, create fallback results
            if not results:
                print(f"Warning: No valid results parsed from LLM response")
                for idx, row in batch_df.iterrows():
                    quote_id = row['response_id'] if 'response_id' in row else f'quote_{idx}'
                    results.append(self._create_enhanced_default_result(quote_id, "No valid results from LLM"))
                    
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"LLM Response preview: {llm_response[:500]}...")
            # Create fallback results for all quotes
            for idx, row in batch_df.iterrows():
                quote_id = row['response_id'] if 'response_id' in row else f'quote_{idx}'
                results.append(self._create_enhanced_default_result(quote_id, f"Parsing error: {str(e)}"))
        
        return results
    
    def _clean_llm_response(self, response_text):
        """Clean and prepare LLM response for JSON parsing"""
        # Remove markdown code blocks
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # Remove any text before the first [
        start_idx = response_text.find('[')
        if start_idx != -1:
            response_text = response_text[start_idx:]
        
        # Remove any text after the last ]
        end_idx = response_text.rfind(']')
        if end_idx != -1:
            response_text = response_text[:end_idx + 1]
        
        # Fix common JSON syntax errors
        # Remove trailing commas before closing braces/brackets
        response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
        
        # Fix missing quotes around property names
        response_text = re.sub(r'(\s*)(\w+)(\s*:)', r'\1"\2"\3', response_text)
        
        # Fix single quotes to double quotes
        response_text = response_text.replace("'", '"')
        
        return response_text.strip()
    
    def _normalize_enhanced_result_fields(self, result):
        """Normalize and validate enhanced result fields with multi-criteria support"""
        try:
            # Ensure basic fields exist
            result.setdefault('quote_id', 'unknown')
            
            # Initialize full relevance scores structure
            full_relevance_scores = {
                'product_capability': 0,
                'implementation_onboarding': 0,
                'integration_technical_fit': 0,
                'support_service_quality': 0,
                'security_compliance': 0,
                'market_position_reputation': 0,
                'vendor_stability': 0,
                'sales_experience_partnership': 0,
                'commercial_terms': 0,
                'speed_responsiveness': 0
            }
            
            # Update with provided relevance scores
            if 'relevance_scores' in result and isinstance(result['relevance_scores'], dict):
                for criterion, score in result['relevance_scores'].items():
                    if criterion in full_relevance_scores:
                        full_relevance_scores[criterion] = int(score) if score is not None else 0
            
            result['relevance_scores'] = full_relevance_scores
            
            # Initialize criterion sentiments
            criterion_sentiments = {}
            if 'criterion_sentiments' in result and isinstance(result['criterion_sentiments'], dict):
                for criterion, sentiment in result['criterion_sentiments'].items():
                    if criterion in full_relevance_scores and full_relevance_scores[criterion] > 0:
                        criterion_sentiments[criterion] = sentiment
            
            result['criterion_sentiments'] = criterion_sentiments
            
            # Calculate primary, secondary, tertiary criteria
            criteria_with_scores = [(criterion, score) for criterion, score in full_relevance_scores.items() if score > 0]
            criteria_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            result['primary_criterion'] = criteria_with_scores[0][0] if criteria_with_scores else 'product_capability'
            result['secondary_criterion'] = criteria_with_scores[1][0] if len(criteria_with_scores) > 1 else None
            result['tertiary_criterion'] = criteria_with_scores[2][0] if len(criteria_with_scores) > 2 else None
            
            # Calculate overall sentiment
            if not result.get('overall_sentiment') or result['overall_sentiment'] == 'neutral':
                result['overall_sentiment'] = self._calculate_enhanced_overall_sentiment(
                    full_relevance_scores, criterion_sentiments
                )
            
            # Set defaults for other fields
            result.setdefault('priority', 'medium')
            result.setdefault('confidence', 'medium')
            result.setdefault('explanation', '')
            
            return result
            
        except Exception as e:
            print(f"Error normalizing result: {e}")
            return None
    
    def _calculate_enhanced_overall_sentiment(self, relevance_scores, criterion_sentiments):
        """Calculate overall sentiment with enhanced logic"""
        if not criterion_sentiments:
            return 'neutral'
        
        # Weight sentiments by relevance scores
        sentiment_weights = {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'mixed': 0
        }
        
        total_weight = 0
        for criterion, sentiment in criterion_sentiments.items():
            relevance_score = relevance_scores.get(criterion, 0)
            if relevance_score > 0:
                sentiment_weights[sentiment] += relevance_score
                total_weight += relevance_score
        
        if total_weight == 0:
            return 'neutral'
        
        # Find the sentiment with highest weight
        max_sentiment = max(sentiment_weights.items(), key=lambda x: x[1])
        
        # If there's a clear winner (more than 60% of total weight)
        if max_sentiment[1] > total_weight * 0.6:
            return max_sentiment[0]
        else:
            # Check for mixed sentiment
            positive_weight = sentiment_weights['positive']
            negative_weight = sentiment_weights['negative']
            
            if positive_weight > 0 and negative_weight > 0:
                return 'mixed'
            elif positive_weight > negative_weight:
                return 'positive'
            elif negative_weight > positive_weight:
                return 'negative'
            else:
                return 'neutral'
    
    def _create_enhanced_default_result(self, quote_id, explanation):
        """Create an enhanced default result for fallback cases"""
        return {
            'quote_id': quote_id,
            'relevance_scores': {
                'product_capability': 2,
                'implementation_onboarding': 0,
                'integration_technical_fit': 0,
                'support_service_quality': 0,
                'security_compliance': 0,
                'market_position_reputation': 0,
                'vendor_stability': 0,
                'sales_experience_partnership': 0,
                'commercial_terms': 0,
                'speed_responsiveness': 0
            },
            'criterion_sentiments': {
                'product_capability': 'neutral'
            },
            'overall_sentiment': 'neutral',
            'primary_criterion': 'product_capability',
            'secondary_criterion': None,
            'tertiary_criterion': None,
            'priority': 'medium',
            'confidence': 'medium',
            'explanation': explanation
        }
    
    def _save_batch_results_to_database(self, results, client_id):
        """Save batch results to database - Enhanced version with multi-criteria support"""
        if not self.supabase:
            return
        
        print(f"[DEBUG] Saving enhanced batch results: {len(results)} records")
        
        for idx, result in enumerate(results):
            if not isinstance(result, dict):
                print(f"[ERROR] Skipping non-dict result: {result}")
                continue
            
            # Get comprehensive data
            quote_id = result.get('quote_id', '')
            relevance_scores = result.get('relevance_scores', {})
            criterion_sentiments = result.get('criterion_sentiments', {})
            overall_sentiment = result.get('overall_sentiment', 'neutral')
            
            # Save one record per quote with comprehensive data
            enhanced_explanation = {
                'primary_criterion': result.get('primary_criterion'),
                'secondary_criterion': result.get('secondary_criterion'),
                'tertiary_criterion': result.get('tertiary_criterion'),
                'all_relevance_scores': relevance_scores,
                'criterion_sentiments': criterion_sentiments,
                'overall_sentiment': overall_sentiment,
                'explanation': result.get('explanation', ''),
                'priority': result.get('priority', 'medium'),
                'confidence': result.get('confidence', 'medium'),
                'analysis_version': 'enhanced_multi_criteria_v2'
            }
            
            # Calculate primary criterion data
            primary_criterion = result.get('primary_criterion', 'product_capability')
            primary_score = relevance_scores.get(primary_criterion, 0)
            primary_sentiment = criterion_sentiments.get(primary_criterion, 'neutral')
            
            # Apply deal outcome weighting if available
            deal_weighted_score = primary_score
            if 'deal_status' in result:
                deal_status = result['deal_status']
                if deal_status == 'Closed Lost':
                    deal_weighted_score = primary_score * 1.2  # 20% higher weight for lost deals
                elif deal_status == 'Closed Won':
                    deal_weighted_score = primary_score * 0.9  # 10% lower weight for won deals
            
            # Create comprehensive database record
            db_record = {
                'quote_id': quote_id,
                'criterion': primary_criterion,
                'relevance_score': int(primary_score) if primary_score is not None else 0,
                'sentiment': primary_sentiment,
                'priority': result.get('priority', 'medium'),
                'confidence': result.get('confidence', 'medium'),
                'relevance_explanation': json.dumps(enhanced_explanation),
                'deal_weighted_score': float(deal_weighted_score) if deal_weighted_score is not None else 0.0,
                'context_keywords': self._extract_context_keywords(result),
                'question_relevance': 'direct',
                'client_id': client_id,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            try:
                self.supabase.save_stage2_response_labeling(db_record)
                print(f"[SUCCESS] Saved enhanced analysis for quote: {quote_id}")
            except Exception as e:
                print(f"[ERROR] Failed to save quote {quote_id}: {e}")
                continue
    
    def _extract_context_keywords(self, result):
        """Extract context keywords from the analysis result"""
        keywords = []
        
        # Extract keywords from explanation
        explanation = result.get('explanation', '')
        if explanation:
            # Simple keyword extraction - could be enhanced with NLP
            important_words = ['accuracy', 'speed', 'cost', 'ease', 'support', 'integration', 
                             'security', 'compliance', 'reliability', 'performance', 'quality']
            for word in important_words:
                if word.lower() in explanation.lower():
                    keywords.append(word)
        
        # Extract keywords from high-relevance criteria
        relevance_scores = result.get('relevance_scores', {})
        for criterion, score in relevance_scores.items():
            if score >= 3:  # High relevance
                keywords.append(criterion.replace('_', ' '))
        
        return ', '.join(keywords) if keywords else ''
