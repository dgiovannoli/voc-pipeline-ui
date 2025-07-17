#!/usr/bin/env python3
"""
Enhanced Stage 3 Findings Analyzer
Includes industry-agnostic client-specific feedback detection
"""

import os
import json
import logging
import pandas as pd
import re
from typing import List, Dict, Any
import openai
from supabase_database import SupabaseDatabase
from client_specific_classifier import ClientSpecificClassifier

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedStage3FindingsAnalyzer:
    def __init__(self, client_id: str = "Rev"):
        self.client_id = client_id
        self.supabase = SupabaseDatabase()
        
        # Load OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Load enhanced findings prompt
        self.findings_prompt = self._load_enhanced_findings_prompt()
    
    def _load_buried_wins_prompt(self) -> str:
        """Load the Buried Wins prompt for compatibility"""
        try:
            prompt_path = "Context/Buried Wins Finding Production Prompt.txt"
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r') as f:
                    return f.read()
            else:
                return "Buried Wins prompt file not found"
        except Exception as e:
            return f"Error loading Buried Wins prompt: {e}"

    def _load_enhanced_findings_prompt(self) -> str:
        """Load the enhanced findings prompt with client-specific detection"""
        return f"""
You are an expert B2B SaaS win/loss researcher analyzing customer interview data to identify key findings and insights.

ANALYZE FOR {self.client_id.upper()}-SPECIFIC FEEDBACK:

When analyzing findings, look for {self.client_id}-specific feedback even when the name isn't mentioned directly. Consider:

1. **Contextual References:**
   - "they" or "them" when context suggests {self.client_id}
   - "this service" or "your service" when discussing {self.client_id}'s product
   - "the software" or "the tool" when discussing {self.client_id} features

2. **{self.client_id}-Specific Features:**
   - Features unique to or strongly associated with {self.client_id}
   - Workflows specific to {self.client_id}'s product
   - Pricing models specific to {self.client_id}

3. **{self.client_id}-Specific Problems:**
   - Issues with {self.client_id}'s specific technology
   - Concerns about {self.client_id}'s pricing or model
   - Integration gaps with {self.client_id}'s platform

When you detect {self.client_id}-specific feedback (even without the name), label the finding as "{self.client_id}-specific" and preserve the specific feedback rather than generalizing it to market trends.

Examples:
- "Speaker identification is an issue" → {self.client_id}-specific (if about {self.client_id}'s feature)
- "Accuracy is more important than speed" → Market trend (if general preference)
- "The turnaround time is great" → {self.client_id}-specific (if about {self.client_id}'s service)
- "Transcription services need to be accurate" → Market trend (if general statement)

ANALYZE THE FOLLOWING CUSTOMER INTERVIEW DATA:

{{findings_data}}

Generate findings that are:
1. Specific and actionable
2. Supported by direct customer quotes
3. Relevant to business decisions
4. Properly labeled as {self.client_id}-specific or market trends

For each finding, provide:
- Finding ID (F1, F2, etc.)
- Finding statement (clear, specific, actionable)
- Primary quote (direct customer quote)
- Secondary quote (if available)
- Classification (COMPETITIVE VULNERABILITY, REVENUE THREAT, MARKET OPPORTUNITY)
- Priority level (High, Medium, Low)
- Enhanced confidence score (1-5)
- Client-specific flag (true if {self.client_id}-specific, false if market trend)

Output in JSON format.
"""

    def _detect_client_specific_feedback(self, quote: str, interview_context: str) -> bool:
        """Detect client-specific feedback using dynamic pattern matching"""
        
        # Direct client mentions (case-insensitive)
        direct_mentions = [self.client_id.lower(), self.client_id.title(), self.client_id.upper()]
        
        # Universal contextual indicators (work across industries)
        universal_indicators = [
            # Pronouns when context suggests the client
            'they', 'them', 'their service', 'their tool', 'their platform',
            'this service', 'this tool', 'this platform', 'this software',
            'your service', 'your tool', 'your platform', 'your software',
            
            # Universal workflow patterns
            'upload and get back', 'send to', 'process and return',
            'subscription model', 'monthly fee', 'usage patterns',
            'integration with', 'connects to', 'works with'
        ]
        
        quote_lower = quote.lower()
        context_lower = interview_context.lower()
        
        # Check for direct mentions
        if any(mention in quote_lower for mention in direct_mentions):
            return True
        
        # Check for universal indicators
        if any(indicator in quote_lower for indicator in universal_indicators):
            return self._validate_client_context(quote, context_lower)
        
        return False

    def _validate_client_context(self, quote: str, context: str) -> bool:
        """Validate if contextual reference is likely about the specific client"""
        
        # Positive indicators for client-specific context (universal)
        client_indicators = [
            # Specific feature mentions (not hardcoded by industry)
            'feature', 'functionality', 'capability', 'tool', 'function',
            'accuracy', 'speed', 'cost', 'efficiency', 'quality',
            'integration', 'workflow', 'process', 'automation',
            
            # Specific experience mentions
            'used it', 'tried it', 'tested it', 'implemented it',
            'deployed it', 'rolled it out', 'adopted it'
        ]
        
        # Negative indicators (suggests general market, not specific client)
        general_indicators = [
            'market', 'industry', 'vendors', 'competitors',
            'general', 'overall', 'typically', 'usually',
            'most services', 'other tools', 'alternatives',
            'in general', 'broadly', 'generally'
        ]
        
        quote_lower = quote.lower()
        context_lower = context.lower()
        
        # Count positive vs negative indicators
        client_score = sum(1 for indicator in client_indicators if indicator in quote_lower or indicator in context_lower)
        general_score = sum(1 for indicator in general_indicators if indicator in quote_lower or indicator in context_lower)
        
        return client_score > general_score

    def _detect_specificity_patterns(self, quote: str) -> bool:
        """Detect client-specific patterns without hardcoding features"""
        
        # Patterns that suggest specific client feedback
        specificity_patterns = [
            # Specific feature mentions
            r'\b(this|that|the)\s+\w+\s+(feature|function|tool|capability)\b',
            r'\b(accuracy|speed|cost|quality|efficiency)\s+(of|with|in)\s+\w+\b',
            
            # Specific experience mentions
            r'\b(used|tried|tested|implemented|deployed)\s+(it|this|that)\b',
            r'\b(worked|functioned|performed)\s+(well|poorly|great|terrible)\b',
            
            # Specific problem mentions
            r'\b(issue|problem|bug|glitch|error)\s+(with|in)\s+\w+\b',
            r'\b(doesn\'t|doesn\'t|won\'t|can\'t)\s+\w+\b',
            
            # Specific integration mentions
            r'\b(integrates|connects|works)\s+(with|to)\s+\w+\b',
            r'\b(integration|connection|compatibility)\s+(with|to)\s+\w+\b'
        ]
        
        quote_lower = quote.lower()
        
        # Check if quote matches specificity patterns
        for pattern in specificity_patterns:
            if re.search(pattern, quote_lower):
                return True
        
        return False

    def _detect_client_specific_with_llm(self, quote: str) -> bool:
        """Use LLM to detect if feedback is client-specific"""
        
        prompt = f"""
        Analyze this customer quote and determine if it's specific to {self.client_id} or general market feedback.
        
        Quote: "{quote}"
        Client: {self.client_id}
        
        Consider:
        1. Does this quote mention {self.client_id} directly or indirectly?
        2. Does this quote refer to specific features, workflows, or experiences with {self.client_id}?
        3. Does this quote discuss {self.client_id}'s pricing, integration, or user experience?
        4. Or is this general feedback about the market/industry that could apply to any vendor?
        
        Respond with only: "CLIENT_SPECIFIC" or "MARKET_GENERAL"
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
            
            return "CLIENT_SPECIFIC" in response.choices[0].message.content
        except Exception as e:
            logger.warning(f"LLM detection failed: {e}")
            return False

    def _enhance_finding_with_client_context(self, finding_data: Dict) -> Dict:
        """Add client-specific context to findings when appropriate"""
        
        quote = finding_data.get('primary_quote', '')
        
        # Use multiple detection methods
        is_specific_pattern = self._detect_specificity_patterns(quote)
        is_specific_llm = self._detect_client_specific_with_llm(quote)
        is_direct_mention = self.client_id.lower() in quote.lower()
        is_contextual = self._detect_client_specific_feedback(quote, quote)
        
        # If any method detects client-specific feedback
        if is_specific_pattern or is_specific_llm or is_direct_mention or is_contextual:
            finding_data['client_specific'] = True
            finding_data['finding_statement'] = f"{self.client_id}-specific: {finding_data.get('finding_statement', '')}"
            finding_data['client_feedback'] = quote
            logger.info(f"Marked finding as {self.client_id}-specific: {finding_data.get('finding_id', '')}")
        else:
            finding_data['client_specific'] = False
        
        return finding_data

    def _get_findings_json(self) -> str:
        """Convert findings to JSON format for LLM processing"""
        try:
            # Get findings from database
            findings = self.supabase.get_stage3_findings_list(self.client_id)
            
            if not findings:
                logger.warning(f"No Stage 3 findings found for client {self.client_id}")
                return ""
            
            # Convert to JSON format
            findings_json = json.dumps(findings, indent=2)
            logger.info(f"📊 Prepared {len(findings)} findings in JSON format")
            
            return findings_json
            
        except Exception as e:
            logger.error(f"❌ Error getting findings JSON: {e}")
            return ""

    def _call_enhanced_findings_analysis(self, findings_json: str) -> str:
        """Call LLM for enhanced findings analysis with client-specific detection"""
        try:
            prompt = self.findings_prompt.format(findings_data=findings_json)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ Error calling enhanced findings analysis: {e}")
            return ""

    def _parse_enhanced_findings(self, findings_text: str) -> List[Dict]:
        """Parse enhanced findings output with client-specific detection"""
        try:
            # Try to parse as JSON first
            if findings_text.strip().startswith('{'):
                findings_data = json.loads(findings_text)
                if isinstance(findings_data, dict) and 'findings' in findings_data:
                    findings = findings_data['findings']
                else:
                    findings = [findings_data]
            else:
                # Fallback to text parsing
                findings = self._parse_findings_text(findings_text)
            
            # Enhance each finding with client-specific detection
            enhanced_findings = []
            for finding in findings:
                enhanced_finding = self._enhance_finding_with_client_context(finding)
                enhanced_findings.append(enhanced_finding)
            
            return enhanced_findings
            
        except Exception as e:
            logger.error(f"❌ Error parsing enhanced findings: {e}")
            return []

    def _parse_findings_text(self, findings_text: str) -> List[Dict]:
        """Parse findings from text format (fallback)"""
        findings = []
        
        # Simple text parsing as fallback
        sections = findings_text.split('---')
        
        for section in sections:
            if not section.strip():
                continue
                
            try:
                lines = section.strip().split('\n')
                finding = {}
                
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        finding[key.strip()] = value.strip()
                
                if finding:
                    findings.append(finding)
                    
            except Exception as e:
                logger.warning(f"Error parsing finding section: {e}")
                continue
        
        return findings

    def _save_enhanced_findings(self, findings: List[Dict]) -> bool:
        """Save enhanced findings to database"""
        try:
            for finding in findings:
                # Prepare finding data for database
                finding_data = {
                    'finding_id': finding.get('finding_id', ''),
                    'finding_statement': finding.get('finding_statement', ''),
                    'primary_quote': finding.get('primary_quote', ''),
                    'secondary_quote': finding.get('secondary_quote', ''),
                    'classification': finding.get('classification', ''),
                    'priority_level': finding.get('priority_level', 'Medium'),
                    'enhanced_confidence': finding.get('enhanced_confidence', 3),
                    'client_specific': finding.get('client_specific', False),
                    'client_feedback': finding.get('client_feedback', ''),
                    'client_id': self.client_id
                }
                
                # Save to database
                success = self.supabase.save_enhanced_finding(finding_data, self.client_id)
                if not success:
                    logger.error(f"Failed to save finding {finding.get('finding_id', '')}")
                    return False
            
            logger.info(f"Successfully saved {len(findings)} enhanced findings")
            return True
            
        except Exception as e:
            logger.error(f"Error saving enhanced findings: {e}")
            return False

    def analyze_enhanced_findings(self) -> bool:
        """Main method to analyze findings with client-specific detection"""
        try:
            logger.info(f"🎯 Starting Enhanced Stage 3 findings analysis for client: {self.client_id}")
            
            # Get findings from database
            findings = self.supabase.get_stage3_findings_list(self.client_id)
            
            if not findings:
                logger.warning(f"No Stage 3 findings found for client {self.client_id}")
                return False
            
            logger.info(f"📊 Found {len(findings)} findings to analyze")
            
            # Convert findings to JSON
            findings_json = self._get_findings_json()
            if not findings_json:
                logger.warning("No findings data available")
                return False
            
            # Enhanced Findings Analysis with client-specific detection
            logger.info("🔄 Enhanced findings analysis with client-specific detection...")
            findings_output = self._call_enhanced_findings_analysis(findings_json)
            if not findings_output:
                logger.error("❌ Enhanced analysis failed - no findings generated")
                return False
            
            # Parse findings and apply client-specific detection
            enhanced_findings = self._parse_enhanced_findings(findings_output)
            if not enhanced_findings:
                logger.warning("No enhanced findings parsed from output")
                return False
            
            # Save enhanced findings to database
            success = self._save_enhanced_findings(enhanced_findings)
            
            if success:
                logger.info(f"✅ Enhanced Stage 3 findings analysis completed successfully for client {self.client_id}")
                
                # Run client-specific classification as final step
                logger.info("🔍 Running client-specific classification...")
                classifier = ClientSpecificClassifier(self.client_id)
                classification_success = classifier.classify_findings()
                
                if classification_success:
                    logger.info(f"✅ Client-specific classification completed successfully for {self.client_id}")
                else:
                    logger.warning(f"⚠️ Client-specific classification failed for {self.client_id}")
                
                return True
            else:
                logger.error(f"❌ Failed to save enhanced findings for client {self.client_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error in enhanced findings analysis: {e}")
            return False

def main():
    """Main function to run enhanced Stage 3 findings analysis"""
    import sys
    
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    else:
        client_id = 'Rev'  # Default client
    
    analyzer = EnhancedStage3FindingsAnalyzer(client_id)
    success = analyzer.analyze_enhanced_findings()
    
    if success:
        print(f"✅ Enhanced Stage 3 findings analysis completed successfully for {client_id}")
    else:
        print(f"❌ Enhanced Stage 3 findings analysis failed for {client_id}")

if __name__ == "__main__":
    main() 