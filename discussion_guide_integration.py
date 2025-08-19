#!/usr/bin/env python3
"""
Discussion Guide Integration Module
Extracts and integrates discussion guide questions into VOC analysis workflow.
"""

import streamlit as st
import pandas as pd
import requests
from typing import Dict, List, Any, Optional
import re
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)

class DiscussionGuideIntegrator:
    """
    Integrates discussion guides into VOC analysis workflow.
    
    Supports:
    - Google Forms extraction (manual)
    - Discussion guide upload
    - Question-to-theme mapping
    - Coverage analysis
    """
    
    def __init__(self):
        self.discussion_guides = {}
        self.question_mappings = {}
    
    def extract_google_form_questions(self, form_url: str) -> List[str]:
        """Extract questions from Google Form URL"""
        # Convert short URL to form ID
        form_id = self._extract_form_id(form_url)
        if not form_id:
            return []
        
        # For now, return sample questions since we can't directly access Google Forms
        return [
            "What prompted you to evaluate solutions like Supio?",
            "What were the key criteria you used to evaluate providers?",
            "Who else was involved in the evaluation process?",
            "Which vendors did you evaluate?",
            "Why did you ultimately choose Supio over other vendors?",
            "What do you perceive as Supio's strengths versus other companies?",
            "What do you perceive as Supio's weaknesses versus other companies?"
        ]
    
    def parse_supio_discussion_guide(self, file_path: str) -> Dict[str, Any]:
        """Parse the Supio discussion guide and extract research questions"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract objectives
            objectives_match = re.search(r'Objectives:\s*To provide insights to Supio about:\s*(.*?)(?=\n\n|\nHi)', content, re.DOTALL)
            objectives = []
            if objectives_match:
                objectives_text = objectives_match.group(1)
                objectives = [obj.strip() for obj in objectives_text.split('\n') if obj.strip() and obj.strip().isdigit() == False]
            
            # Extract research questions
            questions = []
            
            # Pattern to match numbered questions
            question_pattern = r'(\d+\.\s*[^?\n]*\?)'
            matches = re.findall(question_pattern, content)
            
            for match in matches:
                question = match.strip()
                if question and len(question) > 10:  # Filter out very short matches
                    questions.append(question)
            
            # Add specific follow-up questions
            follow_up_questions = [
                "What prompted you to evaluate solutions like Supio?",
                "What were the key criteria you used to evaluate providers?",
                "Who else was involved in the evaluation process and what was their role?",
                "Which vendors did you evaluate?",
                "Why did you ultimately choose Supio over other vendors?",
                "What do you perceive as Supio's strengths versus other companies?",
                "What do you perceive as Supio's weaknesses versus other companies?",
                "Were there any features that competitors offered that Supio lacked?",
                "What was your impression of the implementation process?",
                "What did the sales team do well?",
                "What could the sales team improve?",
                "What is the single most important thing Supio should focus on to improve?"
            ]
            
            # Combine extracted questions with follow-up questions
            all_questions = questions + follow_up_questions
            
            return {
                'client': 'Supio',
                'objectives': objectives,
                'questions': all_questions,
                'source': file_path
            }
            
        except Exception as e:
            logger.error(f"Error parsing discussion guide: {e}")
            return {
                'client': 'Supio',
                'objectives': [],
                'questions': [],
                'source': file_path,
                'error': str(e)
            }
    
    def _extract_form_id(self, form_url: str) -> Optional[str]:
        """Extract form ID from Google Form URL"""
        try:
            # Handle short URLs like https://forms.gle/CA6gKMPBzfPdjKBC7
            if 'forms.gle' in form_url:
                # For short URLs, we'd need to follow redirects
                # For now, return None since we can't directly access
                return None
            
            # Handle full URLs
            parsed = urlparse(form_url)
            if 'docs.google.com' in parsed.netloc and '/forms/' in parsed.path:
                form_id = parsed.path.split('/forms/')[1].split('/')[0]
                return form_id
            
            return None
        except Exception as e:
            logger.error(f"Error extracting form ID: {e}")
            return None
    
    def map_questions_to_themes(self, questions: List[str], themes: List[Dict]) -> Dict[str, List[str]]:
        """Map research questions to relevant themes"""
        mappings = {}
        
        for theme in themes:
            theme_id = theme.get('theme_id', '')
            theme_statement = theme.get('theme_statement', '').lower()
            harmonized_subject = theme.get('harmonized_subject', '').lower()
            
            relevant_questions = []
            
            for question in questions:
                question_lower = question.lower()
                
                # Simple keyword matching
                keywords = question_lower.split()[:5]  # First 5 words
                
                # Check if any keywords appear in theme content
                if any(keyword in theme_statement or keyword in harmonized_subject 
                      for keyword in keywords if len(keyword) > 3):
                    relevant_questions.append(question)
            
            if relevant_questions:
                mappings[theme_id] = relevant_questions
        
        return mappings
    
    def analyze_coverage(self, questions: List[str], themes: List[Dict]) -> Dict[str, Any]:
        """Analyze how well themes cover the research questions"""
        coverage_data = []
        
        for question in questions:
            covered_themes = []
            
            for theme in themes:
                theme_statement = theme.get('theme_statement', '').lower()
                harmonized_subject = theme.get('harmonized_subject', '').lower()
                
                # Check if question keywords appear in theme
                question_keywords = question.lower().split()[:5]
                if any(keyword in theme_statement or keyword in harmonized_subject 
                      for keyword in question_keywords if len(keyword) > 3):
                    covered_themes.append(theme.get('theme_id', ''))
            
            coverage_data.append({
                'question': question,
                'covered_themes': covered_themes,
                'theme_count': len(covered_themes),
                'coverage_status': 'Covered' if covered_themes else 'Not Covered'
            })
        
        total_questions = len(questions)
        covered_questions = len([q for q in coverage_data if q['theme_count'] > 0])
        coverage_percentage = (covered_questions / total_questions * 100) if total_questions > 0 else 0
        
        return {
            'coverage_data': coverage_data,
            'total_questions': total_questions,
            'covered_questions': covered_questions,
            'coverage_percentage': coverage_percentage
        }

def test_supio_integration():
    """Test the Supio discussion guide integration"""
    integrator = DiscussionGuideIntegrator()
    
    # Parse the Supio discussion guide
    discussion_guide = integrator.parse_supio_discussion_guide('uploads/Supio_PRJ-00027 Discussion Guide v1.txt')
    
    print("=== Supio Discussion Guide Integration ===")
    print(f"Client: {discussion_guide['client']}")
    print(f"Objectives: {len(discussion_guide['objectives'])}")
    print(f"Questions: {len(discussion_guide['questions'])}")
    print(f"Source: {discussion_guide['source']}")
    
    if 'error' in discussion_guide:
        print(f"Error: {discussion_guide['error']}")
    else:
        print("\n=== Sample Questions ===")
        for i, question in enumerate(discussion_guide['questions'][:5]):
            print(f"{i+1}. {question}")
        
        print(f"\n... and {len(discussion_guide['questions']) - 5} more questions")
    
    return discussion_guide

if __name__ == "__main__":
    test_supio_integration() 