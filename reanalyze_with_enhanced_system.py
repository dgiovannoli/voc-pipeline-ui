#!/usr/bin/env python3
"""
Force re-analysis of existing quotes with enhanced subject-driven system
This will overwrite the old problematic analysis with our improved routing.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_subject_driven_stage2 import SubjectDrivenStage2Analyzer
from supabase_database import SupabaseDatabase
import logging

def force_reanalyze_client(client_id: str, max_responses: int = None):
    """Force re-analysis of all quotes for a client with enhanced system"""
    
    print(f"🔄 Force re-analyzing {client_id} with enhanced subject-driven system")
    print("=" * 60)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        # Initialize enhanced analyzer
        analyzer = SubjectDrivenStage2Analyzer()
        db = SupabaseDatabase()
        
        # Get ALL Stage 1 responses (ignore existing analysis)
        print("📊 Getting all Stage 1 responses...")
        all_responses_df = db.get_stage1_data_responses(client_id=client_id)
        
        if all_responses_df.empty:
            print(f"❌ No Stage 1 data found for client {client_id}")
            return False
        
        if max_responses:
            all_responses_df = all_responses_df.head(max_responses)
        
        print(f"🎯 Found {len(all_responses_df)} responses to re-analyze")
        
        # Show subject distribution
        subject_counts = all_responses_df['subject'].value_counts()
        print(f"\n📋 Subject Distribution:")
        for subject, count in subject_counts.head(10).items():
            criterion = analyzer.get_criterion_from_subject(subject)
            quality = analyzer.get_quality_weight(subject)
            print(f"  {subject}: {count} responses → {criterion} (quality: {quality})")
        
        # Confirm re-analysis
        confirm = input(f"\n⚠️  This will OVERWRITE existing analysis for {len(all_responses_df)} responses. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Re-analysis cancelled")
            return False
        
        # Process each response with enhanced system
        print(f"\n🚀 Starting enhanced re-analysis...")
        processed_count = 0
        enhanced_results = []
        
        for idx, row in all_responses_df.iterrows():
            try:
                # Convert row to dict
                response_data = row.to_dict()
                
                # Analyze with enhanced subject-driven routing
                analysis_result = analyzer.analyze_response(response_data)
                
                if analysis_result:
                    # Delete old analysis first (if exists)
                    quote_id = analysis_result.get('quote_id')
                    try:
                        db.supabase.table('stage2_response_labeling').delete().eq('quote_id', quote_id).eq('client_id', client_id).execute()
                    except:
                        pass  # Continue if delete fails (maybe no existing analysis)
                    
                    # Save new enhanced analysis
                    labeling_data = {
                        'quote_id': analysis_result.get('quote_id'),
                        'criterion': analysis_result.get('criterion'),
                        'score': analysis_result.get('relevance_score'),  
                        'sentiment': analysis_result.get('sentiment'),
                        'priority': analysis_result.get('priority'),
                        'confidence': analysis_result.get('confidence'),
                        'relevance_explanation': f"Enhanced subject-driven: {analysis_result.get('relevance_explanation')}",
                        'deal_weighted_score': analysis_result.get('deal_weighted_score'),
                        'context_keywords': analysis_result.get('context_keywords'),
                        'client_id': client_id
                    }
                    
                    success = db.save_stage2_response_labeling(labeling_data)
                    
                    if success:
                        processed_count += 1
                        enhanced_results.append(analysis_result)
                        print(f"✅ Re-analyzed: {analysis_result.get('original_subject')} → {analysis_result.get('criterion')}")
                    else:
                        print(f"❌ Failed to save: {quote_id}")
                
            except Exception as e:
                print(f"❌ Failed to process response {row.get('response_id', 'unknown')}: {e}")
                continue
        
        # Summary
        print(f"\n🎉 Enhanced re-analysis complete!")
        print(f"📊 Successfully processed: {processed_count}/{len(all_responses_df)} responses")
        
        # Show improved criterion distribution
        if enhanced_results:
            criterion_counts = {}
            for result in enhanced_results:
                criterion = result.get('criterion', 'unknown')
                criterion_counts[criterion] = criterion_counts.get(criterion, 0) + 1
            
            print(f"\n📈 Enhanced Criterion Distribution:")
            for criterion, count in sorted(criterion_counts.items()):
                print(f"  {criterion}: {count} responses")
            
            # Compare to old system (all product_capability)
            unique_criteria = len(criterion_counts)
            print(f"\n🎯 Improvement Summary:")
            print(f"  Old system: 1 criterion (all product_capability)")
            print(f"  Enhanced system: {unique_criteria} criteria (intelligent routing)")
            print(f"  Intelligence gain: {unique_criteria-1} additional criteria utilized")
        
        return True
        
    except Exception as e:
        print(f"❌ Re-analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Force re-analysis with enhanced subject-driven system')
    parser.add_argument('client_id', help='Client ID to re-analyze')
    parser.add_argument('--max-responses', type=int, help='Maximum responses to process')
    
    args = parser.parse_args()
    
    success = force_reanalyze_client(args.client_id, args.max_responses)
    
    if success:
        print(f"\n✅ Enhanced re-analysis completed successfully!")
        print(f"💡 Check your Stage 2 results - you should now see diverse criteria instead of all 'product_capability'")
    else:
        print(f"\n❌ Re-analysis failed. Check the logs above for details.")

if __name__ == "__main__":
    main() 