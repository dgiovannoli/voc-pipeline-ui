#!/usr/bin/env python3
"""
Client-Specific Classifier
Post-processes Stage 3 findings to identify client-specific vs market trend findings
"""

import os
import json
import logging
import pandas as pd
from typing import List, Dict, Any
import openai
from supabase_database import SupabaseDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClientSpecificClassifier:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.supabase = SupabaseDatabase()
        
        # Load OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.openai_api_key)
    
    def classify_findings(self) -> bool:
        """Classify all Stage 3 findings as client-specific or market trends"""
        try:
            logger.info(f"🎯 Starting client-specific classification for {self.client_id}")
            
            # Get all Stage 3 findings
            findings = self.supabase.get_stage3_findings(self.client_id)
            if findings.empty:
                logger.warning(f"No Stage 3 findings found for client {self.client_id}")
                return False
            
            logger.info(f"📊 Found {len(findings)} findings to classify")
            
            # Process findings in batches
            classified_findings = []
            batch_size = 10
            
            for i in range(0, len(findings), batch_size):
                batch = findings.iloc[i:i+batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(findings) + batch_size - 1)//batch_size}")
                
                batch_results = self._classify_batch(batch)
                classified_findings.extend(batch_results)
            
            # Update findings in database
            success = self._update_findings_classification(classified_findings)
            
            if success:
                logger.info(f"✅ Successfully classified {len(classified_findings)} findings")
                self._report_classification_summary(classified_findings)
                return True
            else:
                logger.error("❌ Failed to update findings classification")
                return False
                
        except Exception as e:
            logger.error(f"Error in client-specific classification: {e}")
            return False
    
    def _classify_batch(self, batch: pd.DataFrame) -> List[Dict]:
        """Classify a batch of findings using LLM"""
        try:
            # Prepare findings for LLM
            findings_data = []
            for _, finding in batch.iterrows():
                findings_data.append({
                    'finding_id': finding.get('finding_id', ''),
                    'finding_statement': finding.get('finding_statement', ''),
                    'primary_quote': finding.get('primary_quote', ''),
                    'secondary_quote': finding.get('secondary_quote', '')
                })
            
            # Create prompt for classification
            prompt = self._get_classification_prompt(findings_data)
            
            # Call LLM for classification
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.1
            )
            
            classification_text = response.choices[0].message.content
            logger.info("Generated classifications for batch")
            
            # Parse classifications
            classifications = self._parse_classifications(classification_text, findings_data)
            
            return classifications
            
        except Exception as e:
            logger.error(f"Error classifying batch: {e}")
            return []
    
    def _get_classification_prompt(self, findings_data: List[Dict]) -> str:
        """Get prompt for client-specific classification"""
        return f"""
You are an expert B2B SaaS researcher analyzing customer interview findings for a win/loss analysis pipeline. Your task is to classify each finding as either:

- {self.client_id}-specific: Feedback about {self.client_id}'s product, service, features, workflows, pricing, or user experience.
- Market trend: General feedback that could apply to any vendor in the space.

**In this dataset, a finding is {self.client_id}-specific if:**
- The quote or statement mentions {self.client_id} by name.
- The quote or statement describes a specific feature, capability, workflow, or user experience that is clearly about {self.client_id}'s product or service.
- The feedback is about a specific problem, benefit, limitation, or suggestion that is unique to {self.client_id}'s offering.
- The context of the interview makes it clear that "the software," "the tool," "they," "their service," etc. refers to {self.client_id}.

**A finding is Market trend if:**
- It discusses general industry preferences, concerns, or behaviors.
- It could apply to any vendor in the space.
- It's about broader market opportunities or competitive landscape.
- It's a general workflow or process observation.

**Classification Rules:**
- If the quote or finding is about a specific feature, capability, or experience that is clearly about {self.client_id}'s product, classify as {self.client_id}-specific, even if the name is not mentioned.
- If your reasoning says "this is about {self.client_id}'s service/product/feature," you MUST classify as {self.client_id}-specific.
- If the feedback is a general industry concern, preference, or trend, classify as Market trend.
- If you are unsure, err on the side of classifying as {self.client_id}-specific.

**CRITICAL:** If the finding mentions any specific feature, capability, workflow, or user experience that could be unique to {self.client_id}'s product, classify it as {self.client_id}-specific. Only classify as Market trend if the feedback is clearly about general industry preferences or behaviors that could apply to any vendor.

**Contrasting Examples:**
Example 1:
Quote: "The speaker identification is inaccurate."
Context: The interview is about {self.client_id}.
Reasoning: This is about a specific feature of {self.client_id}'s platform.
Classification: {self.client_id}-specific

Example 2:
Quote: "Speaker identification is important in transcription services."
Context: General industry discussion.
Reasoning: This is a general market trend.
Classification: Market trend

Example 3:
Quote: "The turnaround time is great."
Context: The interview is about {self.client_id}.
Reasoning: This is about {self.client_id}'s service.
Classification: {self.client_id}-specific

Example 4:
Quote: "Data security is important for legal tech."
Reasoning: This is a general market concern.
Classification: Market trend

**For each finding, output EXACTLY this format:**
---
Finding ID: [finding_id]
Classification: [{self.client_id}-specific OR Market trend]
Reasoning: [Your reasoning. If you say 'this is about {self.client_id}'s service/product/feature,' you must classify as {self.client_id}-specific.]
---

**IMPORTANT:** Use the exact text "{self.client_id}-specific" or "Market trend" in your Classification line. Do not use any other variations.

**FINDINGS TO CLASSIFY:**

{json.dumps(findings_data, indent=2)}

Classify each finding and provide your reasoning.
"""
    
    def _parse_classifications(self, classification_text: str, findings_data: List[Dict]) -> List[Dict]:
        """Parse LLM classifications"""
        classifications = []
        
        # Debug: Log the raw classification text
        logger.info(f"Raw classification text: {classification_text[:500]}...")
        
        # Split by finding sections
        sections = classification_text.split('---')
        
        for section in sections[1:]:  # Skip first empty section
            try:
                lines = section.strip().split('\n')
                
                finding_id = ""
                classification = ""
                reasoning = ""
                
                for line in lines:
                    if line.startswith('Finding ID:'):
                        finding_id = line.replace('Finding ID:', '').strip()
                    elif line.startswith('Classification:'):
                        classification = line.replace('Classification:', '').strip()
                    elif line.startswith('Reasoning:'):
                        reasoning = line.replace('Reasoning:', '').strip()
                
                if finding_id and classification:
                    # Find the original finding data
                    original_finding = next((f for f in findings_data if f['finding_id'] == finding_id), None)
                    
                    if original_finding:
                        # More flexible parsing for client-specific classification
                        is_client_specific = (
                            f"{self.client_id}-specific" in classification.lower() or
                            f"{self.client_id} specific" in classification.lower() or
                            f"{self.client_id.lower()}-specific" in classification.lower() or
                            f"{self.client_id.lower()} specific" in classification.lower()
                        )
                        
                        classifications.append({
                            'finding_id': finding_id,
                            'client_specific': is_client_specific,
                            'classification_reasoning': reasoning,
                            'original_finding': original_finding
                        })
                
            except Exception as e:
                logger.warning(f"Error parsing classification section: {e}")
                continue
        
        return classifications
    
    def _update_findings_classification(self, classifications: List[Dict]) -> bool:
        """Update findings in database with classification results"""
        try:
            updated_count = 0
            for classification in classifications:
                finding_id = classification['finding_id']
                is_client_specific = classification['client_specific']
                reasoning = classification['classification_reasoning']
                
                # Determine the classification value
                classification_value = f"{self.client_id}-specific" if is_client_specific else "Market trend"
                
                # Update the finding in database
                success = self.supabase.update_stage3_finding_classification(
                    finding_id=finding_id,
                    classification=classification_value,
                    classification_reasoning=reasoning,
                    client_id=self.client_id
                )
                
                if success:
                    updated_count += 1
                    logger.info(f"✅ Updated finding {finding_id}: {classification_value}")
                else:
                    logger.warning(f"⚠️ Failed to update finding {finding_id}")
            
            logger.info(f"Successfully updated {updated_count}/{len(classifications)} findings in database")
            return updated_count > 0
            
        except Exception as e:
            logger.error(f"Error updating findings classification: {e}")
            return False
    
    def _report_classification_summary(self, classifications: List[Dict]):
        """Report summary of classification results"""
        client_specific_count = sum(1 for c in classifications if c['client_specific'])
        market_trend_count = len(classifications) - client_specific_count
        
        logger.info(f"📊 Classification Summary:")
        logger.info(f"   {self.client_id}-specific findings: {client_specific_count}")
        logger.info(f"   Market trend findings: {market_trend_count}")
        logger.info(f"   Total findings processed: {len(classifications)}")
        
        # Show sample client-specific findings
        client_specific_findings = [c for c in classifications if c['client_specific']]
        if client_specific_findings:
            logger.info(f"🔍 Sample {self.client_id}-specific findings:")
            for i, finding in enumerate(client_specific_findings[:3]):
                logger.info(f"   {i+1}. {finding['finding_id']}: {finding['original_finding']['finding_statement'][:100]}...")
        else:
            logger.warning(f"⚠️  No {self.client_id}-specific findings detected")

def main():
    """Main function to run client-specific classification"""
    import sys
    
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    else:
        client_id = 'Rev'  # Default client
    
    classifier = ClientSpecificClassifier(client_id)
    success = classifier.classify_findings()
    
    if success:
        print(f"✅ Client-specific classification completed successfully for {client_id}")
    else:
        print(f"❌ Client-specific classification failed for {client_id}")

if __name__ == "__main__":
    main() 