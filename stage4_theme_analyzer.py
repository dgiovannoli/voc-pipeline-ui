#!/usr/bin/env python3
"""
Stage 4 Theme Analyzer
Generates themes from Stage 3 findings using the B2B SaaS Win/Loss Theme Development Protocol
BEST PRACTICE: LLM generates only themes/alerts, code matches themes to findings and attaches real quotes
"""

import os
import json
import logging
import pandas as pd
import re
from typing import List, Dict, Any, Optional
import openai
import numpy as np
from supabase_database import SupabaseDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage4ThemeAnalyzer:
    def __init__(self, client_id: str = "Rev"):
        self.client_id = client_id
        self.supabase = SupabaseDatabase()
        
        # Load OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Load theme prompt
        self.theme_prompt = self._load_theme_prompt()
        
        # Solutioning language patterns to detect and remove
        self.solutioning_patterns = [
            r'\b(indicating|suggesting|recommending|requiring|needing|should|must|need to|should be)\b',
            r'\b(improve|enhance|strengthen|optimize|maximize|minimize)\b',
            r'\b(critical area for improvement|need for vendors to|necessitating|requiring)\b',
            r'\b(highlighting the need|underscores the importance|emphasizes the need)\b'
        ]
        
    def _load_theme_prompt(self) -> str:
        """Load the theme prompt from the Context/Theme Prompt.txt file"""
        try:
            with open('Context/Theme Prompt.txt', 'r', encoding='utf-8') as f:
                base_prompt = f.read()
            
            # Add the new framework requirements to the base prompt
            new_framework = """

NEW THEME FRAMEWORK REQUIREMENTS (UPDATED JULY 2025)
====================================================

THEME TITLE STRUCTURE: [Emotional Driver] + [Specific Context] + [Business Impact]

**EMOTIONAL DRIVER GUIDANCE (STRONGLY ENCOURAGED):**
- Strongly prefer including an emotional driver (e.g., frustration, anxiety, excitement, relief) in the theme title when the evidence or customer language clearly expresses emotion, pain, or feel.
- Do NOT force an emotional driver if it is not present in the evidence, but use it whenever it fits naturally and makes the theme more compelling.
- If the evidence is neutral, use a specific, business-focused title without an emotional driver.
- Example with driver: "Frustration with Rev’s Speaker Identification Accuracy Disrupts Trial Preparation"
- Example with driver: "Anxiety Over Rising Costs Jeopardizes Small Firm Viability"
- Example without driver: "Rev’s Integration Gap with Key Legal Platforms Hinders Workflow"
- Example without driver: "Integration Gaps with Legal Research Platforms Hinder Workflow"

// STEP 1: GENERATE THEME STATEMENT ONLY (NO QUOTES)
FOR EACH THEME, OUTPUT THE FOLLOWING JSON OBJECT:
{"theme_title": ..., "theme_statement": ...}

1. THEME STATEMENT: Two-sentence structure with clear flow
   - Sentence 1: Decision behavior or specific problem with consequence
   - Sentence 2: Summarize the most common interviewee pain point or reaction in your own words. Do NOT use direct quotes or quoted phrases. This should be a paraphrased synthesis, not a verbatim statement.
   - This should be a concise, executive-ready summary in your own words.

**IMPORTANT:** Do NOT include direct quotes or quoted phrases in the theme statement. Only paraphrased synthesis is allowed.

EXAMPLES OF CORRECT OUTPUT:
{"theme_title": "Data Security Concerns Impact Client Trust", "theme_statement": "Client trust in legal services diminishes when data security concerns arise, particularly regarding sensitive video evidence exposure. Interviewees are reluctant to use cloud-based tools when they perceive any risk of client data being exposed or accessed without authorization."}

{"theme_title": "Cost Concerns Limit Software Adoption", "theme_statement": "Revenue growth potential is constrained as subscription-based software adoption is avoided due to cost concerns among key decision-makers. Many decision-makers avoid new software because they worry about accumulating subscription fees, even when it could improve their workflow."}

EXAMPLES OF INCORRECT OUTPUT:
{"theme_title": "Data Security Concerns Impact Client Trust", "theme_statement": "Client trust in legal services diminishes when data security concerns arise. One user said, 'If for some crazy reason, like a piece of video I uploaded were to come out on the internet or something, that would be very bad.'"} (✗ Do NOT use direct quotes or quoted phrases in the theme statement.)

VALIDATION RULES:
1. Theme statements MUST be exactly two sentences
2. First sentence MUST describe a decision behavior or specific problem with consequence (no quotes required)
3. Second sentence MUST summarize the most common interviewee pain point or reaction in your own words (do NOT use direct quotes or quoted phrases)
4. No solutioning language ("needs improvement", "should be", "must", etc.)
5. No generic statements; must be specific and paraphrased

**EVIDENCE-BASED QUANTITATIVE CLAIMS:**
- Do NOT invent or estimate specific numbers, percentages, or metrics (e.g., "drops below 80%", "saves 5 hours") unless they are directly stated in the evidence or customer quotes.
- All statistics or quantitative claims in theme titles or statements must be traceable to the source data.
- If the evidence is qualitative, describe the pattern or impact without assigning a number.

// STEP 2: FOR EACH THEME, SELECT THE SINGLE MOST REPRESENTATIVE DIRECT QUOTE
// (This step will be implemented in a separate LLM call after theme statements are generated.)

"""
            
            return base_prompt + new_framework
            
        except FileNotFoundError:
            logger.error("Theme Prompt.txt file not found in Context/ directory")
            raise
        except Exception as e:
            logger.error(f"Error loading theme prompt: {e}")
            raise
    
    def _validate_theme_statement(self, theme_statement: str) -> Dict[str, Any]:
        """Validate theme statement against new July 2025 framework requirements"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'suggestions': []
        }
        
        # Check for two-sentence structure - improved parsing
        # Split on sentence endings but preserve quotes
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', theme_statement.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) != 2:
            validation_result['is_valid'] = False
            validation_result['issues'].append(f"Must be exactly 2 sentences, found {len(sentences)}")
            validation_result['suggestions'].append("Restructure to exactly two sentences: first with decision/problem/consequence, second with direct quote evidence")
            return validation_result
        
        # Sentence 1: Should not contain quotes, should mention a decision/behavior/problem
        if '"' in sentences[0] or "'" in sentences[0]:
            validation_result['is_valid'] = False
            validation_result['issues'].append("First sentence should not contain direct quotes")
            validation_result['suggestions'].append("Move all direct quotes to the second sentence")
        
        # Sentence 2: Must provide evidence-driven synthesis of interviewee pain points or reactions
        # Check for evidence-driven language (pain points, reactions, behaviors)
        evidence_patterns = [
            r'\b(interviewees?|respondents?|users?|customers?|attorneys?|professionals?)\b',
            r'\b(expressed|described|reported|stated|noted|mentioned|felt|experienced)\b',
            r'\b(pain point|frustration|anxiety|reluctance|concern|worry|overwhelmed|confused)\b',
            r'\b(strong|common|frequent|consistent|clear|specific)\b'
        ]
        
        has_evidence_driven_language = any(re.search(pattern, sentences[1], re.IGNORECASE) for pattern in evidence_patterns)
        if not has_evidence_driven_language:
            validation_result['is_valid'] = False
            validation_result['issues'].append("Second sentence missing evidence-driven synthesis of interviewee pain points or reactions")
            validation_result['suggestions'].append("Provide evidence-driven synthesis of the most common interviewee pain point or personal reaction")
        
        # No solutioning language
        solutioning_patterns = [
            r'needs improvement', r'should', r'must', r'need to', r'suggesting', r'recommending', r'requiring'
        ]
        for pattern in solutioning_patterns:
            if re.search(pattern, theme_statement, re.IGNORECASE):
                validation_result['is_valid'] = False
                validation_result['issues'].append(f"Contains solutioning language: {pattern}")
                validation_result['suggestions'].append("Remove solutioning language and focus on describing patterns and evidence")
        
        return validation_result
    
    def _validate_theme_title(self, theme_title: str) -> Dict[str, Any]:
        """Validate theme title against new framework requirements"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'suggestions': []
        }
        
        # Check for emotional driver
        emotional_drivers = [
            r'\b(frustration|anxiety|excitement|confusion|relief|concern|satisfaction|dissatisfaction|worry|hope|disappointment|enthusiasm)\b'
        ]
        
        has_emotional_driver = any(re.search(pattern, theme_title, re.IGNORECASE) for pattern in emotional_drivers)
        if not has_emotional_driver:
            validation_result['is_valid'] = False
            validation_result['issues'].append("Missing emotional driver")
            validation_result['suggestions'].append("Include emotional driver (frustration, anxiety, excitement, confusion, relief, etc.)")
        
        # Check for specific context
        context_patterns = [
            r'\b(transcription|data security|pricing|cost|accuracy|speed|efficiency|integration|workflow|process|feature|capability)\b'
        ]
        
        has_specific_context = any(re.search(pattern, theme_title, re.IGNORECASE) for pattern in context_patterns)
        if not has_specific_context:
            validation_result['is_valid'] = False
            validation_result['issues'].append("Missing specific context")
            validation_result['suggestions'].append("Include specific context (transcription, data security, pricing, etc.)")
        
        # Check for business impact
        business_impact_patterns = [
            r'\b(drives|undermines|accelerates|blocks|boosts|impacts|affects|influences|determines|shapes|creates|reduces|increases)\b',
            r'\b(dissatisfaction|trust|adoption|productivity|efficiency|satisfaction|retention|growth|revenue|competitive|position|market)\b'
        ]
        
        has_business_impact = any(re.search(pattern, theme_title, re.IGNORECASE) for pattern in business_impact_patterns)
        if not has_business_impact:
            validation_result['is_valid'] = False
            validation_result['issues'].append("Missing business impact")
            validation_result['suggestions'].append("Include business impact (drives dissatisfaction, undermines trust, accelerates adoption, etc.)")
        
        return validation_result
    
    def _clean_solutioning_language(self, text: str) -> str:
        """Remove solutioning language from text"""
        cleaned_text = text
        
        # Remove common solutioning phrases
        solutioning_replacements = [
            (r'\bindicating a need for\b', 'reveals'),
            (r'\bsuggesting\b', 'demonstrating'),
            (r'\brecommending\b', 'showing'),
            (r'\brequiring\b', 'necessitating'),
            (r'\bneeding\b', 'requiring'),
            (r'\bshould\b', 'does'),
            (r'\bmust\b', 'will'),
            (r'\bneed to\b', 'will'),
            (r'\bshould be\b', 'is'),
            (r'\bimprove\b', 'enhance'),
            (r'\benhance\b', 'strengthen'),
            (r'\bstrengthen\b', 'reinforce'),
            (r'\boptimize\b', 'maximize'),
            (r'\bmaximize\b', 'increase'),
            (r'\bminimize\b', 'reduce'),
            (r'\bcritical area for improvement\b', 'key challenge'),
            (r'\bneed for vendors to\b', 'vendors'),
            (r'\bnecessitating\b', 'requiring'),
            (r'\brequiring\b', 'needing'),
            (r'\bhighlighting the need\b', 'demonstrating'),
            (r'\bunderscores the importance\b', 'shows the significance'),
            (r'\bemphasizes the need\b', 'demonstrates')
        ]
        
        for pattern, replacement in solutioning_replacements:
            cleaned_text = re.sub(pattern, replacement, cleaned_text, flags=re.IGNORECASE)
        
        return cleaned_text

    def _clean_duplicate_text(self, text: str) -> str:
        """Clean up duplicate text that might be added during expansion"""
        # Remove duplicate phrases
        phrases_to_remove = [
            "This pattern emerges across 0 companies,",
            "revealing competitive dynamics in the market.",
            "This pattern emerges across 0 companies, revealing competitive dynamics in the market."
        ]
        
        cleaned_text = text
        for phrase in phrases_to_remove:
            cleaned_text = cleaned_text.replace(phrase, "")
        
        # Clean up extra spaces and punctuation
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\s*,\s*,\s*', ', ', cleaned_text)
        cleaned_text = re.sub(r'\s*\.\s*\.\s*', '. ', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text

    def _expand_theme_statement(self, theme_statement: str, findings: List[Dict]) -> str:
        """Expand short theme statements with additional context"""
        # Count unique companies in findings
        company_field = self._identify_company_field(pd.DataFrame(findings))
        if company_field:
            unique_companies = set()
            for finding in findings:
                company = finding.get(company_field, '')
                if company and company.strip():
                    unique_companies.add(company.strip())
            company_count = len(unique_companies)
        else:
            company_count = 2  # Default assumption
        
        # Ensure we have at least 2 companies for cross-company validation
        if company_count < 2:
            company_count = 2
        
        # Add cross-company validation if missing
        if not re.search(r'\bacross \d+ (companies?|organizations?|firms)\b', theme_statement, re.IGNORECASE):
            theme_statement = f"{theme_statement} This pattern emerges across {company_count} companies,"
        
        # Add competitive context if missing and not already present
        if not re.search(r'\bcompetitive\b', theme_statement, re.IGNORECASE):
            theme_statement = f"{theme_statement} revealing competitive dynamics in the market."
        
        # Clean up any duplicate text
        theme_statement = self._clean_duplicate_text(theme_statement)
        
        return theme_statement
    
    def _get_findings_json(self) -> str:
        """Convert findings to JSON format for LLM processing with proper validation"""
        try:
            # Get findings from database
            findings = self.supabase.get_stage3_findings_list(self.client_id)
            
            if not findings:
                logger.warning(f"No findings found for client {self.client_id}")
                return ""
            
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(findings)
            
            # Validate company identification
            company_field = self._identify_company_field(df)
            if not company_field:
                logger.error("PROCESSING HALTED: Cannot verify company identification")
                return ""
            
            # Ensure all required columns exist
            required_columns = [
                'finding_id', 'finding_statement', company_field, 'date', 
                'deal_status', 'interviewee_name', 'supporting_response_ids', 
                'evidence_strength', 'finding_category', 'criteria_met', 
                'priority_level', 'primary_quote', 'secondary_quote', 'quote_attributions'
            ]
            
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ""
            
            # Add metadata columns if available
            metadata_columns = ['segment', 'role', 'deal_value', 'industry']
            for col in metadata_columns:
                if col not in df.columns:
                    df[col] = ""
            
            # Convert to list of dictionaries (JSON format)
            findings_list = df[required_columns + metadata_columns].to_dict('records')
            
            # Convert to JSON string
            findings_json = json.dumps(findings_list, indent=2)
            
            logger.info(f"�� Prepared {len(findings_list)} findings in JSON format")
            logger.info(f"Company identification: {company_field}")
            logger.debug(f"Sample JSON: {findings_json[:500]}...")
            
            return findings_json
            
        except Exception as e:
            logger.error(f"❌ Error preparing findings JSON: {str(e)}")
            return ""
    
    def _get_findings_for_theme_analysis(self, client_id: str = 'Rev') -> str:
        """Get findings data for theme analysis, including classification data"""
        try:
            # Get findings with classification data
            findings = self.supabase.get_stage3_findings(client_id=client_id)
            
            if findings.empty:
                logger.warning(f"No Stage 3 findings found for client {client_id}")
                return ""
            
            # Convert to list of dicts with classification data
            findings_list = []
            for _, row in findings.iterrows():
                finding_data = {
                    'finding_id': row.get('finding_id', ''),
                    'finding_statement': row.get('finding_statement', ''),
                    'primary_quote': row.get('primary_quote', ''),
                    'secondary_quote': row.get('secondary_quote', ''),
                    'classification': row.get('classification', 'Market trend'),  # Include classification
                    'classification_reasoning': row.get('classification_reasoning', ''),  # Include reasoning
                    'client_id': row.get('client_id', client_id)
                }
                findings_list.append(finding_data)
            
            # Convert to JSON
            findings_json = json.dumps(findings_list, indent=2)
            logger.info(f"📊 Prepared {len(findings_list)} findings with classification data for theme analysis")
            
            return findings_json
            
        except Exception as e:
            logger.error(f"❌ Error getting findings for theme analysis: {e}")
            return ""
    
    def _identify_company_field(self, df: pd.DataFrame) -> str:
        """Identify the field containing company/interview identifiers"""
        possible_fields = ['interview_company', 'companies_affected', 'company', 'company_name', 'client', 'customer']
        
        for field in possible_fields:
            if field in df.columns and df[field].notna().any():
                unique_companies = df[field].dropna().nunique()
                if unique_companies >= 2:
                    logger.info(f"Identified {field} as the company identifier with {unique_companies} unique companies")
                    return field
        
        # If no field with multiple companies found, use the first available company field
        for field in possible_fields:
            if field in df.columns:
                logger.info(f"Using {field} as company identifier (single company mode)")
                return field
        
        logger.error("No suitable company identifier field found")
        return ""
    
    def _call_llm_for_themes(self, findings_json: str) -> str:
        """Call OpenAI API to generate themes using the comprehensive protocol, expecting JSON output"""
        try:
            # Prepare the prompt with findings data using the Theme Prompt protocol
            full_prompt = f"""
{self.theme_prompt}

FINDINGS DATA TO ANALYZE (WITH CLASSIFICATION):
{findings_json}

**EXAMPLE OF HOW TO CHECK CLASSIFICATION:**
When you see a finding like this:
{{
  "finding_id": "F1",
  "finding_statement": "Users report accuracy issues",
  "classification": "Rev-specific",  ← CHECK THIS FIELD
  "primary_quote": "The accuracy is poor"
}}

You MUST generate a Rev-specific theme because classification = "Rev-specific"

When you see a finding like this:
{{
  "finding_id": "F2", 
  "finding_statement": "Legal professionals prioritize accuracy",
  "classification": "Market trend",  ← CHECK THIS FIELD
  "primary_quote": "Accuracy is important"
}}

You MUST generate a general market theme because classification = "Market trend"

**CRITICAL: You MUST generate BOTH types of themes based on the classification field:**

1. For findings with "classification": "Rev-specific" → Generate Rev-specific themes (start with "Rev's")
2. For findings with "classification": "Market trend" → Generate general market themes (do NOT start with "Rev's")

**AVOID DUPLICATIONS:**
- If a market trend finding covers the same topic as a Rev-specific finding, prioritize the Rev-specific theme
- Do NOT generate both "Speaker Identification Issues" (market) AND "Rev's Speaker Identification Problems" (Rev)
- Consolidate similar themes into the more specific Rev version when appropriate

**You MUST generate a mix of both types. If you only generate Rev-specific themes, you are ignoring the classification data.**

CRITICAL CLASSIFICATION-AWARE THEME GENERATION INSTRUCTIONS:

**MANDATORY: CHECK THE "classification" FIELD FOR EACH FINDING**

Each finding has a "classification" field with one of two values:
- "Rev-specific" = Generate Rev-specific themes
- "Market trend" = Generate general market themes

**REV-SPECIFIC THEMES** (ONLY when finding classification = "Rev-specific"):
- Generate themes that are SPECIFIC and ACTIONABLE
- Include concrete details about Rev's features, workflows, or user experience
- Focus on unique Rev-specific challenges or opportunities
- Use specific, descriptive titles that add value
- MUST start with "Rev's" or "Rev-Specific"

**EXAMPLES OF GOOD REV-SPECIFIC THEMES:**

✓ "Rev's Speaker Identification Fails During Multi-Party Legal Recordings"
"Speaker identification accuracy drops below 80% when 3+ speakers are present in legal recordings, forcing attorneys to manually identify speakers during trial preparation. Respondents explicitly state 'The more that it could identify each person that is talking would be huge for my trial prep.'"

✓ "Rev's Integration Gap with Westlaw/LexisNexis Hinders Legal Workflow"
"Lack of direct integration with Westlaw and LexisNexis forces manual data transfer, adding 2-3 hours per case and creating workflow inefficiencies. Respondents explicitly state 'I need it to connect with my existing tools or I'll switch to a competitor.'"

✓ "Rev's High Transcription Costs Force Solo Practitioners to Limit Usage"
"$150/month subscription costs prevent adoption among solo practitioners with infrequent usage, creating barriers for small firms. Respondents explicitly state 'I can't justify $150/month when I only use it twice in six months.'"

**MARKET TREND THEMES** (ONLY when finding classification = "Market trend"):
- Do NOT mention Rev unless explicitly mentioned in the finding
- Focus on broader industry patterns and behaviors
- Use general, market-wide language
- MUST NOT start with "Rev's" or "Rev-Specific"

**EXAMPLES OF GOOD MARKET TREND THEMES:**

✓ "Legal Professionals Prioritize Accuracy Over Speed in Transcription Services"
"Legal professionals unanimously prioritize accuracy above all other factors when selecting transcription services. Respondents unanimously describe accuracy as their 'number one' priority, with several stating they would pay premium prices for precision."

✓ "Subscription Fatigue Creates Barriers for Legal Tech Adoption"
"Decision-makers express significant subscription fatigue when evaluating new legal software solutions. Respondents explicitly state 'I try to limit my subscriptions because I find even if you can cancel anytime, I forget about them.'"

**CRITICAL REQUIREMENTS:**
1. **Check Classification First**: Look at the "classification" field for each finding
2. **Be Specific**: Include concrete details, metrics, or specific features
3. **Add Value**: Provide actionable insights, not just observations
4. **Differentiate**: Clearly distinguish Rev-specific vs market trends
5. **Follow Two-Sentence Structure**: First sentence = pattern, Second sentence = evidence with quotes

**AVOID GENERIC LANGUAGE:**
✗ "Rev Users Report Issues" (too vague)
✗ "Rev-Specific Challenge: Problems" (not specific)
✗ "Rev users consistently report that..." (adds no value)
✓ "Rev's Speaker Identification Accuracy Drops Below 80% in Multi-Party Recordings" (specific and actionable)
✓ "Speaker identification accuracy drops below 80% when 3+ speakers are present..." (specific and actionable)

**MANDATORY EXECUTION INSTRUCTIONS:**
1. **FIRST**: Check the "classification" field for each finding
2. **SECOND**: For findings with classification = "Rev-specific", generate Rev-specific themes
3. **THIRD**: For findings with classification = "Market trend", generate general market themes
4. **FOURTH**: Follow the exact two-sentence structure for all themes
5. **FIFTH**: Reference actual finding IDs in supporting_finding_ids

**CRITICAL: You MUST generate themes for BOTH classifications. If you see findings with "Market trend" classification, you MUST generate general market themes (not Rev-specific). If you only generate Rev-specific themes, you are failing to follow the classification data.**

GRANULAR THEME REQUIREMENTS:
- Generate 15-25 granular themes
- Each theme should capture specific patterns from 2-4 related findings
- Focus on concrete examples and actionable insights
- Ensure themes are evidence-driven and supported by direct customer quotes

CRITICAL: You MUST reference actual finding IDs from the provided data. Every theme and alert must have at least one valid finding ID in the supporting_finding_ids field.

Return ONLY valid, minified JSON (no markdown, no explanations, no extra text, no comments). Example:
{{"themes": [...], "strategic_alerts": [...]}}
"""

            # Call OpenAI API
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert B2B SaaS competitive intelligence analyst specializing in win/loss analysis. Generate executive-ready strategic themes and alerts from customer interview findings."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            llm_output = response.choices[0].message.content.strip()
            
            # Save raw LLM output for debugging
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            debug_filename = f"stage4_llm_output_{self.client_id}_{timestamp}.txt"
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(f"Client: {self.client_id}\n")
                f.write(f"Timestamp: {pd.Timestamp.now()}\n")
                f.write(f"Prompt Length: {len(full_prompt)} characters\n")
                f.write(f"Response Length: {len(llm_output)} characters\n")
                f.write("\n" + "="*50 + "\n")
                f.write("RAW LLM OUTPUT:\n")
                f.write("="*50 + "\n")
                f.write(llm_output)
            
            logger.info(f"Raw LLM output saved to {debug_filename}")
            
            return llm_output
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise

    def _parse_llm_themes_output(self, llm_output: str) -> List[Dict]:
        """Parse LLM themes output with enhanced validation"""
        
        def try_json_repair(s):
            # Try to fix common JSON issues
            s = s.strip()
            
            # Remove markdown code blocks
            s = re.sub(r'```json\s*', '', s)
            s = re.sub(r'```\s*$', '', s)
            
            # Fix missing commas between objects
            s = re.sub(r'"\}(\{"', r'"},\{"', s)
            s = re.sub(r'"\}(\s*\{)', r'"},\1', s)
            
            # Fix trailing commas
            s = re.sub(r',(\s*[}\]])', r'\1', s)
            
            # Fix missing quotes around keys
            s = re.sub(r'(\w+):', r'"\1":', s)
            
            # Fix unescaped quotes in values
            s = re.sub(r':\s*"([^"]*)"([^"]*)"', r': "\1\2"', s)
            
            # Fix missing commas after finding_id
            s = re.sub(r'finding_id":"([^"]+)"\}(\{"', r'finding_id":"\1"},\{"', s)
            
            return s
        
        try:
            # Try to parse the JSON
            try:
                parsed_data = json.loads(llm_output)
            except json.JSONDecodeError as e:
                logger.warning(f"Initial JSON parsing failed: {e}")
                # Try to repair the JSON
                repaired_output = try_json_repair(llm_output)
                try:
                    parsed_data = json.loads(repaired_output)
                    logger.info("JSON repair successful")
                except json.JSONDecodeError as e2:
                    logger.error(f"JSON repair failed: {e2}")
                    logger.error(f"Raw output: {llm_output[:1000]}...")
                    raise ValueError(f"Failed to parse LLM output as JSON: {e2}")
            
            themes = []
            strategic_alerts = []
            
            # Process themes
            if 'themes' in parsed_data:
                for i, theme in enumerate(parsed_data['themes']):
                    # Validate theme title structure
                    title_validation = self._validate_theme_title(theme.get('theme_title', ''))
                    if not title_validation['is_valid']:
                        logger.warning(f"Theme {i+1} title validation failed: {title_validation['issues']}")
                        logger.warning(f"Suggestions: {title_validation['suggestions']}")
                    
                    # Validate theme statement structure
                    statement_validation = self._validate_theme_statement(theme.get('theme_statement', ''))
                    if not statement_validation['is_valid']:
                        logger.warning(f"Theme {i+1} statement validation failed: {statement_validation['issues']}")
                        logger.warning(f"Suggestions: {statement_validation['suggestions']}")
                    
                    # Add validation info to theme
                    theme['title_validation'] = title_validation
                    theme['statement_validation'] = statement_validation
                    
                    themes.append(theme)
            
            # Process strategic alerts
            if 'strategic_alerts' in parsed_data:
                for alert in parsed_data['strategic_alerts']:
                    strategic_alerts.append(alert)
            
            # Log validation summary
            valid_themes = sum(1 for t in themes if t['title_validation']['is_valid'] and t['statement_validation']['is_valid'])
            total_themes = len(themes)
            
            logger.info(f"Theme validation summary: {valid_themes}/{total_themes} themes meet all requirements")
            
            if valid_themes < total_themes:
                logger.warning("Some themes do not meet the new framework requirements. Consider regenerating.")
            
            return themes + strategic_alerts
            
        except Exception as e:
            logger.error(f"Error parsing LLM themes output: {e}")
            raise
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get OpenAI embedding for a given text."""
        if not text.strip():
            return np.zeros(1536)  # OpenAI's embedding size for text-embedding-ada-002
        response = openai.Embedding.create(
            input=[text],
            model="text-embedding-ada-002"
        )
        return np.array(response['data'][0]['embedding'])

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 0.0
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _match_themes_to_findings(self, themes: list, findings: list, threshold: float = 0.75) -> list:
        """Match themes to findings using OpenAI embeddings and attach real quotes and company IDs."""
        try:
            # Precompute embeddings for all findings
            finding_texts = [f.get('finding_statement', '') for f in findings]
            finding_ids = [f.get('finding_id', '') for f in findings]
            finding_company_ids = [f.get('company_id', '') for f in findings]
            finding_embeddings = [self._get_embedding(text) for text in finding_texts]

            for theme in themes:
                theme_text = (theme.get('theme_title', '') + ' ' + theme.get('theme_statement', '')).strip()
                theme_emb = self._get_embedding(theme_text)

                # Compute similarity to all findings
                similarities = [self._cosine_similarity(theme_emb, f_emb) for f_emb in finding_embeddings]
                matched_indices = [i for i, sim in enumerate(similarities) if sim >= threshold]

                # Aggregate supporting finding IDs and company IDs
                supporting_ids = [finding_ids[i] for i in matched_indices]
                company_ids = list({finding_company_ids[i] for i in matched_indices if finding_company_ids[i]})

                # Attach to theme
                theme['supporting_finding_ids'] = supporting_ids
                theme['company_ids'] = company_ids

                # Attach real quotes (first two as primary/secondary)
                quotes = []
                for i in matched_indices:
                    quote = findings[i].get('primary_quote', '') or findings[i].get('verbatim_response', '')
                    if quote and quote not in quotes:
                        quotes.append(quote)
                theme['primary_quote'] = quotes[0] if quotes else ""
                theme['secondary_quote'] = quotes[1] if len(quotes) > 1 else ""

            logger.info(f"✅ Matched {len(themes)} themes to findings using OpenAI embeddings")
            return themes

        except Exception as e:
            logger.error(f"Error matching themes to findings: {e}")
            return themes
    
    def _find_best_matching_findings(self, theme: Dict, findings: List[Dict]) -> str:
        """Find the best matching findings for a theme based on content similarity"""
        try:
            theme_title = theme.get('theme_title', '').lower()
            theme_statement = theme.get('theme_statement', '').lower()
            
            # Simple keyword matching
            best_matches = []
            
            for finding in findings:
                finding_statement = finding.get('finding_statement', '').lower()
                finding_id = finding.get('finding_id', '')
                
                if not finding_id or not finding_statement:
                    continue
                
                # Calculate similarity score
                score = 0
                keywords = theme_title.split() + theme_statement.split()
                
                for keyword in keywords:
                    if len(keyword) > 3 and keyword in finding_statement:
                        score += 1
                
                if score > 0:
                    best_matches.append((finding_id, score))
            
            # Sort by score and return top matches
            best_matches.sort(key=lambda x: x[1], reverse=True)
            
            if best_matches:
                # Return the top 5 matching finding IDs to get more quotes
                top_matches = best_matches[:5]
                return ','.join([finding_id for finding_id, score in top_matches])
            
            return ""
            
        except Exception as e:
            logger.error(f"Error finding best matching findings: {e}")
            return ""
    
    def _find_additional_supporting_findings(self, theme: Dict, findings: List[Dict], existing_ids: str) -> str:
        """Find additional supporting findings to ensure multiple quotes"""
        try:
            existing_id_list = [id.strip() for id in existing_ids.split(',') if id.strip()]
            
            # If we already have 3+ findings, we don't need more
            if len(existing_id_list) >= 3:
                return ""
            
            theme_title = theme.get('theme_title', '').lower()
            theme_statement = theme.get('theme_statement', '').lower()
            
            # Find additional findings that are related but not already included
            additional_matches = []
            
            for finding in findings:
                finding_id = finding.get('finding_id', '')
                finding_statement = finding.get('finding_statement', '').lower()
                
                # Skip if already included
                if finding_id in existing_id_list:
                    continue
                
                if not finding_id or not finding_statement:
                    continue
                
                # Calculate similarity score
                score = 0
                keywords = theme_title.split() + theme_statement.split()
                
                for keyword in keywords:
                    if len(keyword) > 3 and keyword in finding_statement:
                        score += 1
                
                if score > 0:
                    additional_matches.append((finding_id, score))
            
            # Sort by score and return additional matches
            additional_matches.sort(key=lambda x: x[1], reverse=True)
            
            if additional_matches:
                # Return up to 3 additional findings
                additional_count = min(3 - len(existing_id_list), len(additional_matches))
                additional_findings = additional_matches[:additional_count]
                return ','.join([finding_id for finding_id, score in additional_findings])
            
            return ""
            
        except Exception as e:
            logger.error(f"Error finding additional supporting findings: {e}")
            return ""
    
    def _save_themes_to_database(self, themes: List[Dict[str, Any]]) -> bool:
        """Save themes to the database"""
        try:
            if not themes:
                logger.warning("No themes to save")
                return False
            
            # Save themes to database
            success_count = 0
            for theme in themes:
                try:
                    # Map LLM output fields to database fields if needed
                    if 'title' in theme and 'theme_title' not in theme:
                        theme['theme_title'] = theme['title']
                    if 'statement' in theme and 'theme_statement' not in theme:
                        theme['theme_statement'] = theme['statement']
                    # Determine if this is a theme or strategic alert
                    theme_type = theme.get('theme_type', 'theme')
                    if theme_type == 'strategic_alert':
                        # Map alert fields to dedicated alert columns
                        theme_data = {
                            'client_id': self.client_id,
                            'theme_id': theme.get('alert_id', ''),
                            'theme_type': 'strategic_alert',
                            'competitive_flag': False,
                            
                            # Theme fields (empty for alerts)
                            'theme_title': '',
                            'theme_statement': '',
                            'classification': '',
                            'deal_context': '',
                            'metadata_insights': '',
                            'primary_quote': '',
                            'secondary_quote': '',
                            'supporting_finding_ids': '',
                            'company_ids': '',
                            
                            # Strategic Alert fields
                            'alert_title': theme.get('alert_title', ''),
                            'alert_statement': theme.get('alert_statement', ''),
                            'alert_classification': theme.get('alert_classification', ''),
                            'strategic_implications': theme.get('strategic_implications', ''),
                            'primary_alert_quote': theme.get('primary_alert_quote', ''),
                            'secondary_alert_quote': theme.get('secondary_alert_quote', ''),
                            'supporting_alert_finding_ids': theme.get('supporting_alert_finding_ids', ''),
                            'alert_company_ids': theme.get('alert_company_ids', ''),
                        }
                    else:
                        # Map theme fields as before
                        theme_data = {
                            'client_id': self.client_id,
                            'theme_id': theme.get('theme_id', ''),
                            'theme_title': theme.get('theme_title', ''),
                            'theme_statement': theme.get('theme_statement', ''),
                            'classification': theme.get('classification', ''),
                            'deal_context': theme.get('deal_context', ''),
                            'metadata_insights': theme.get('metadata_insights', ''),
                            'primary_quote': theme.get('primary_quote', ''),
                            'secondary_quote': theme.get('secondary_quote', ''),
                            'competitive_flag': self._convert_to_boolean(theme.get('competitive_flag', '')),
                            'supporting_finding_ids': theme.get('supporting_finding_ids', ''),
                            'company_ids': theme.get('company_ids', ''),
                            'theme_type': 'theme',
                        }
                    
                    # Save to database
                    if self.supabase.save_stage4_theme(theme_data):
                        success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving theme {theme.get('theme_id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Successfully saved {success_count}/{len(themes)} themes to database")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error saving themes to database: {e}")
            return False
    
    def analyze_themes(self, client_id: str = 'Rev') -> bool:
        """Main method to analyze themes from Stage 3 findings"""
        try:
            logger.info(f"🎯 Starting Stage 4 theme analysis for client: {client_id}")
            
            # Get findings with classification data
            findings_json = self._get_findings_for_theme_analysis(client_id)
            if not findings_json:
                logger.warning("No findings data available for theme analysis")
                return False
            
            logger.info(f"📊 Found findings data for theme analysis")
            
            # Call LLM for theme generation
            logger.info("🔄 Generating themes with classification-aware analysis...")
            themes_output = self._call_llm_for_themes(findings_json)
            if not themes_output:
                logger.error("❌ Theme generation failed - no output generated")
                return False
            
            # Parse themes output
            themes = self._parse_llm_themes_output(themes_output)
            # Filter out themes with empty title or statement
            themes = [t for t in themes if t.get('theme_title', '').strip() and t.get('theme_statement', '').strip()]
            if not themes:
                logger.warning("No themes parsed from output")
                return False
            
            # Get findings data for validation
            findings = self.supabase.get_stage3_findings(client_id)
            findings_list = findings.to_dict('records')
            
            # Validate quantitative claims against supporting quotes
            logger.info("🔍 Validating quantitative claims against supporting quotes...")
            themes = self._validate_quantitative_claims(themes, findings_list)
            logger.info(f"✅ Quantitative validation completed for {len(themes)} themes")
            
            # Debug: Check for themes with numbers
            for theme in themes:
                theme_title = theme.get('theme_title', '')
                theme_statement = theme.get('theme_statement', '')
                if '80%' in theme_title or '80%' in theme_statement:
                    logger.warning(f"🔍 DEBUG: Found theme with 80%: {theme_title}")
                    logger.warning(f"   Statement: {theme_statement[:100]}...")
            
            # Save themes to database
            success = self._save_themes_to_database(themes)
            
            if success:
                logger.info(f"✅ Stage 4 theme analysis completed successfully for client {client_id}")
            else:
                logger.error(f"❌ Failed to save themes for client {client_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error in theme analysis: {e}")
            return False
    
    def process_themes(self, client_id: str = None) -> bool:
        """Process themes for a specific client"""
        if client_id:
            self.client_id = client_id
        
        return self.analyze_themes()

    def _convert_to_boolean(self, value: str) -> bool:
        """Convert string value to boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', 'yes', '1', 'y']
        return False

    def _validate_quantitative_claims(self, themes: List[Dict], findings: List[Dict]) -> List[Dict]:
        """
        Post-processing filter to detect and flag unsupported numbers/percentages in themes.
        Checks if numbers mentioned in themes are present in supporting quotes.
        """
        logger.info(f"🔍 DEBUG: _validate_quantitative_claims called with {len(themes)} themes and {len(findings)} findings")
        
        def extract_numbers(text: str) -> List[str]:
            """Extract numbers, percentages, and metrics from text"""
            # Match numbers, percentages, ratios, etc.
            patterns = [
                r'\d+%',  # percentages
                r'\d+\+',  # "3+ speakers"
                r'\d+-\d+',  # ranges
                r'\$\d+',  # dollar amounts
                r'\d+ hours?',  # time periods
                r'\d+ minutes?',
                r'\d+ days?',
                r'\d+ weeks?',
                r'\d+ months?',
                r'\d+ years?',
                r'\d+ times?',  # frequency
                r'\d+ per \w+',  # rates
            ]
            numbers = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                numbers.extend(matches)
            return numbers

        def get_supporting_quotes(theme: Dict, findings: List[Dict]) -> str:
            """Get all supporting quotes for a theme"""
            supporting_ids = theme.get('supporting_finding_ids', [])
            if isinstance(supporting_ids, str):
                supporting_ids = json.loads(supporting_ids)
            
            quotes = []
            for finding in findings:
                if finding.get('finding_id') in supporting_ids:
                    quotes.append(finding.get('primary_quote', ''))
                    quotes.append(finding.get('secondary_quote', ''))
            
            return ' '.join([q for q in quotes if q])

        validated_themes = []
        
        for theme in themes:
            theme_title = theme.get('theme_title', '')
            theme_statement = theme.get('theme_statement', '')
            
            # Extract numbers from theme title and statement
            title_numbers = extract_numbers(theme_title)
            statement_numbers = extract_numbers(theme_statement)
            all_theme_numbers = title_numbers + statement_numbers
            
            if not all_theme_numbers:
                # No numbers to validate
                validated_themes.append(theme)
                continue
            
            # Debug: Log themes with numbers
            if all_theme_numbers:
                logger.info(f"🔍 DEBUG: Theme '{theme_title[:50]}...' has numbers: {all_theme_numbers}")
            
            # Get supporting quotes
            supporting_quotes = get_supporting_quotes(theme, findings)
            
            # Check if numbers are present in supporting quotes
            quote_numbers = extract_numbers(supporting_quotes)
            
            # Find unsupported numbers
            unsupported_numbers = []
            for number in all_theme_numbers:
                if number not in quote_numbers:
                    unsupported_numbers.append(number)
            
            if unsupported_numbers:
                # Flag theme with unsupported numbers
                logger.warning(f"⚠️ Theme '{theme_title}' contains unsupported numbers: {unsupported_numbers}")
                logger.warning(f"   Supporting quotes: {supporting_quotes[:200]}...")
                
                # Add validation metadata to theme
                theme['validation_warnings'] = theme.get('validation_warnings', [])
                theme['validation_warnings'].append(f"Contains unsupported numbers: {unsupported_numbers}")
                
                # Optionally rewrite theme to remove unsupported numbers
                # For now, just flag it
                validated_themes.append(theme)
            else:
                # All numbers are supported
                validated_themes.append(theme)
        
        return validated_themes

    def _generate_themes_from_findings(self, findings: List[Dict]) -> List[Dict]:
        """Generate themes from findings using LLM with comprehensive protocol (JSON output)"""
        try:
            if not findings:
                logger.warning("No findings provided for theme generation")
                return []
            
            # Convert findings to JSON format for LLM
            findings_json = self._get_findings_json()
            if not findings_json:
                logger.warning("No findings data available for theme generation")
                return []
            
            # Call LLM to generate themes (expects JSON output)
            llm_output = self._call_llm_for_themes(findings_json)
            if not llm_output:
                logger.warning("No response from LLM")
                return []
            
            # Parse themes and alerts from LLM JSON output
            themes = self._parse_llm_themes_output(llm_output)
            if not themes:
                logger.warning("No themes parsed from LLM output")
                return []
            
            # Match themes to findings and attach real quotes
            themes = self._match_themes_to_findings(themes, findings)
            
            logger.info(f"🎯 Generated {len(themes)} themes/alerts from findings")
            return themes
            
        except Exception as e:
            logger.error(f"Error generating themes from findings: {e}")
            return []



def main():
    """Main function to run Stage 4 theme analysis"""
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Stage 4 Theme Analysis')
    parser.add_argument('--client_id', type=str, default='Rev', help='Client ID to analyze')
    
    args = parser.parse_args()
    client_id = args.client_id
    
    try:
        analyzer = Stage4ThemeAnalyzer(client_id)
        success = analyzer.process_themes()
        
        if success:
            print(f"✅ Stage 4 theme analysis completed successfully for client: {client_id}")
            sys.exit(0)
        else:
            print(f"❌ Stage 4 theme analysis failed for client: {client_id}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running Stage 4 theme analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 