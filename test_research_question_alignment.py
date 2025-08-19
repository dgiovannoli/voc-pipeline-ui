#!/usr/bin/env python3
"""
Test Research Question Alignment with Supio Data
Analyzes how well current responses align with research questions from discussion guide.
"""

import pandas as pd
import json
from typing import Dict, List, Any
from discussion_guide_integration import DiscussionGuideIntegrator
from supabase_database import SupabaseDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchQuestionAlignmentTester:
    """Test research question alignment with existing data"""
    
    def __init__(self):
        self.db = SupabaseDatabase()
        self.integrator = DiscussionGuideIntegrator()
        
    def load_supio_discussion_guide(self) -> Dict[str, Any]:
        """Load Supio discussion guide"""
        return self.integrator.parse_supio_discussion_guide('uploads/Supio_PRJ-00027 Discussion Guide v1.txt')
    
    def get_supio_responses(self) -> pd.DataFrame:
        """Get Supio responses from database"""
        # Get all responses and filter for any client with responses
        responses = self.db.get_stage1_data_responses(client_id='default')
        
        if responses.empty:
            # Try to get any available responses
            print("   ⚠️  No responses found for 'default' client, trying 'supio'...")
            responses = self.db.get_stage1_data_responses(client_id='supio')
        
        if responses.empty:
            print("   ⚠️  No responses found in database. Using sample data for testing...")
            # Create sample data for testing
            sample_responses = [
                {
                    'response_id': 'test_1',
                    'verbatim_response': 'We chose Rev because of their accuracy and speed in legal transcription. The pricing was competitive and the turnaround time was excellent.',
                    'company': 'Supio Legal',
                    'interviewee_name': 'John Doe',
                    'sentiment': 'positive',
                    'impact_score': 4,
                    'harmonized_subject': 'product_features'
                },
                {
                    'response_id': 'test_2',
                    'verbatim_response': 'The implementation process was smooth and the support team was very helpful. We were able to get started quickly.',
                    'company': 'Supio Legal',
                    'interviewee_name': 'Jane Smith',
                    'sentiment': 'positive',
                    'impact_score': 5,
                    'harmonized_subject': 'implementation'
                },
                {
                    'response_id': 'test_3',
                    'verbatim_response': 'We compared several transcription services and Rev stood out for their accuracy and legal compliance features.',
                    'company': 'Supio Legal',
                    'interviewee_name': 'Bob Wilson',
                    'sentiment': 'positive',
                    'impact_score': 4,
                    'harmonized_subject': 'competitive_analysis'
                }
            ]
            responses = pd.DataFrame(sample_responses)
        
        return responses
    
    def analyze_response_alignment(self, responses: pd.DataFrame, research_questions: List[str]) -> Dict[str, Any]:
        """Analyze how well responses align with research questions"""
        
        alignment_results = {
            'total_responses': len(responses),
            'total_questions': len(research_questions),
            'aligned_responses': 0,
            'question_coverage': {},
            'response_alignments': [],
            'uncovered_questions': [],
            'coverage_summary': {}
        }
        
        # Initialize question coverage
        for question in research_questions:
            alignment_results['question_coverage'][question] = {
                'matching_responses': 0,
                'response_ids': [],
                'keywords_found': []
            }
        
        # Analyze each response
        for _, response in responses.iterrows():
            response_text = response['verbatim_response'].lower()
            response_id = response['response_id']
            
            # Check alignment with each research question
            response_alignments = []
            
            for question in research_questions:
                question_lower = question.lower()
                
                # Simple keyword matching (could be enhanced with LLM)
                keywords = self._extract_keywords(question_lower)
                matches = []
                
                for keyword in keywords:
                    if keyword in response_text:
                        matches.append(keyword)
                
                if matches:
                    alignment_score = len(matches) / len(keywords)
                    if alignment_score > 0.3:  # 30% keyword match threshold
                        response_alignments.append({
                            'question': question,
                            'alignment_score': alignment_score,
                            'keywords_matched': matches
                        })
                        
                        # Update question coverage
                        alignment_results['question_coverage'][question]['matching_responses'] += 1
                        alignment_results['question_coverage'][question]['response_ids'].append(response_id)
                        alignment_results['question_coverage'][question]['keywords_found'].extend(matches)
            
            # Record response alignment
            alignment_results['response_alignments'].append({
                'response_id': response_id,
                'response_text': response['verbatim_response'][:100] + "...",
                'company': response['company'],
                'interviewee': response['interviewee_name'],
                'sentiment': response['sentiment'],
                'impact_score': response['impact_score'],
                'harmonized_subject': response['harmonized_subject'],
                'alignments': response_alignments,
                'has_alignment': len(response_alignments) > 0
            })
            
            if response_alignments:
                alignment_results['aligned_responses'] += 1
        
        # Identify uncovered questions
        for question, coverage in alignment_results['question_coverage'].items():
            if coverage['matching_responses'] == 0:
                alignment_results['uncovered_questions'].append(question)
        
        # Calculate coverage summary
        alignment_results['coverage_summary'] = {
            'total_responses': len(responses),
            'aligned_responses': alignment_results['aligned_responses'],
            'alignment_percentage': (alignment_results['aligned_responses'] / len(responses)) * 100,
            'questions_with_coverage': len([q for q, c in alignment_results['question_coverage'].items() if c['matching_responses'] > 0]),
            'total_questions': len(research_questions),
            'coverage_percentage': (len([q for q, c in alignment_results['question_coverage'].items() if c['matching_responses'] > 0]) / len(research_questions)) * 100
        }
        
        return alignment_results
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common words and extract keywords
        stop_words = {'what', 'how', 'why', 'when', 'where', 'who', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        
        words = text.split()
        keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 3]
        return list(set(keywords))  # Remove duplicates
    
    def print_alignment_report(self, results: Dict[str, Any]):
        """Print comprehensive alignment report"""
        
        print("=" * 80)
        print("🔍 RESEARCH QUESTION ALIGNMENT ANALYSIS")
        print("=" * 80)
        
        # Overall Summary
        summary = results['coverage_summary']
        print(f"\n📊 OVERALL COVERAGE SUMMARY:")
        print(f"   Total Responses: {summary['total_responses']}")
        print(f"   Aligned Responses: {summary['aligned_responses']} ({summary['alignment_percentage']:.1f}%)")
        print(f"   Questions with Coverage: {summary['questions_with_coverage']}/{summary['total_questions']} ({summary['coverage_percentage']:.1f}%)")
        
        # Question Coverage Details
        print(f"\n📋 QUESTION COVERAGE DETAILS:")
        for question, coverage in results['question_coverage'].items():
            if coverage['matching_responses'] > 0:
                print(f"   ✅ {question}")
                print(f"      Matching Responses: {coverage['matching_responses']}")
                print(f"      Keywords Found: {', '.join(set(coverage['keywords_found']))}")
            else:
                print(f"   ❌ {question}")
        
        # Uncovered Questions
        if results['uncovered_questions']:
            print(f"\n⚠️  UNCOVERED QUESTIONS ({len(results['uncovered_questions'])}):")
            for question in results['uncovered_questions']:
                print(f"   • {question}")
        
        # Sample Aligned Responses
        aligned_responses = [r for r in results['response_alignments'] if r['has_alignment']]
        if aligned_responses:
            print(f"\n🎯 SAMPLE ALIGNED RESPONSES:")
            for i, response in enumerate(aligned_responses[:5]):  # Show first 5
                print(f"   {i+1}. Response ID: {response['response_id']}")
                print(f"      Text: {response['response_text']}")
                print(f"      Alignments: {len(response['alignments'])} questions")
                for alignment in response['alignments']:
                    print(f"         - {alignment['question'][:50]}... (Score: {alignment['alignment_score']:.2f})")
                print()
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if summary['alignment_percentage'] < 50:
            print("   • Consider enhancing Stage 2 with research question alignment")
            print("   • Add keyword-based matching to response labeling")
        if summary['coverage_percentage'] < 70:
            print("   • Significant research question gaps detected")
            print("   • Consider additional data collection for uncovered questions")
        if summary['alignment_percentage'] > 70:
            print("   • Good response alignment - current approach may be sufficient")
            print("   • Focus on theme-level optimization")

def main():
    """Run the research question alignment test"""
    tester = ResearchQuestionAlignmentTester()
    
    # Load discussion guide
    print("📖 Loading Supio discussion guide...")
    discussion_guide = tester.load_supio_discussion_guide()
    research_questions = discussion_guide['questions']
    print(f"   Loaded {len(research_questions)} research questions")
    
    # Get Supio responses
    print("\n📊 Loading Supio responses from database...")
    responses = tester.get_supio_responses()
    print(f"   Found {len(responses)} responses")
    
    # Analyze alignment
    print("\n🔍 Analyzing response-question alignment...")
    results = tester.analyze_response_alignment(responses, research_questions)
    
    # Print report
    tester.print_alignment_report(results)
    
    # Save detailed results
    with open('supio_alignment_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Detailed results saved to: supio_alignment_analysis.json")

if __name__ == "__main__":
    main() 