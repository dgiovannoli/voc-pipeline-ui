#!/usr/bin/env python3
"""
Deployment script for redesigned Stage 2 system
"""

import os
import json
from redesigned_stage2_analyzer import RedesignedStage2Analyzer
from supabase_database import SupabaseDatabase

def deploy_redesigned_system():
    """Deploy the redesigned Stage 2 system"""
    
    print("🚀 DEPLOYING REDESIGNED STAGE 2 SYSTEM")
    print("=" * 50)
    
    # Configuration
    client_id = "Rev"
    batch_size = 20  # Conservative batch size for production
    max_workers = 2  # Conservative parallel processing
    
    print(f"📋 Configuration:")
    print(f"   Client ID: {client_id}")
    print(f"   Batch Size: {batch_size}")
    print(f"   Max Workers: {max_workers}")
    
    # Initialize analyzer
    print(f"\n🔧 Initializing redesigned analyzer...")
    analyzer = RedesignedStage2Analyzer(client_id, batch_size, max_workers)
    
    # Check current data
    db = SupabaseDatabase()
    current_data = db.get_stage2_response_labeling(client_id)
    
    print(f"\n📊 Current System Status:")
    print(f"   Existing records: {len(current_data)}")
    
    if not current_data.empty:
        print(f"   Missing relevance scores: {current_data['relevance_score'].isna().sum()}")
        print(f"   Product capability over-reliance: {(current_data['criterion'] == 'product_capability').sum() / len(current_data) * 100:.1f}%")
    
    # Get quotes to process
    quotes_df = db.get_stage1_quotes(client_id)
    
    if quotes_df.empty:
        print(f"❌ No quotes found for processing")
        return {"error": "No quotes found"}
    
    print(f"\n📝 Quotes to Process:")
    print(f"   Total quotes: {len(quotes_df)}")
    print(f"   Estimated batches: {(len(quotes_df) + batch_size - 1) // batch_size}")
    
    # Confirm deployment
    print(f"\n⚠️  DEPLOYMENT WARNING:")
    print(f"   This will replace existing Stage 2 analysis")
    print(f"   Estimated processing time: {len(quotes_df) * 2 / 60:.1f} minutes")
    print(f"   Estimated cost: ${len(quotes_df) * 0.002:.2f} (based on GPT-4o-mini)")
    
    # Process quotes
    print(f"\n🔄 Starting redesigned analysis...")
    
    try:
        results = analyzer.process_quotes(client_id)
        
        if 'error' in results:
            print(f"❌ Processing failed: {results['error']}")
            return results
        
        print(f"\n✅ Processing Complete!")
        print(f"   Total quotes processed: {results['total_quotes_processed']}")
        print(f"   Successful analyses: {results['successful_analyses']}")
        print(f"   Success rate: {results['successful_analyses'] / results['total_quotes_processed'] * 100:.1f}%")
        
        # Quality report
        quality_report = results.get('quality_report', {})
        if quality_report and 'error' not in quality_report:
            summary = quality_report.get('summary', {})
            print(f"\n📊 Quality Report:")
            print(f"   Success rate: {summary.get('success_rate', 0):.1f}%")
            print(f"   Average relevance score: {summary.get('average_relevance_score', 0):.2f}")
            
            quality_indicators = quality_report.get('quality_indicators', {})
            print(f"   Criteria coverage: {quality_indicators.get('criteria_coverage', 0)}/10")
            print(f"   Sentiment diversity: {quality_indicators.get('sentiment_diversity', 0)} levels")
            print(f"   High confidence rate: {quality_indicators.get('high_confidence_rate', 0):.1f}%")
        
        # Verify results
        print(f"\n🔍 Verifying results...")
        new_data = db.get_stage2_response_labeling(client_id)
        
        if not new_data.empty:
            print(f"✅ Verification successful!")
            print(f"   Total records in database: {len(new_data)}")
            print(f"   Records with relevance scores: {new_data['relevance_score'].notna().sum()}")
            print(f"   Relevance score coverage: {new_data['relevance_score'].notna().sum() / len(new_data) * 100:.1f}%")
            
            # Show criteria distribution
            criteria_dist = new_data['criterion'].value_counts()
            print(f"\n📋 Criteria Distribution:")
            for criterion, count in criteria_dist.head(5).items():
                pct = count / len(new_data) * 100
                print(f"   {criterion}: {count} ({pct:.1f}%)")
            
            # Show sentiment distribution
            sentiment_dist = new_data['sentiment'].value_counts()
            print(f"\n🎭 Sentiment Distribution:")
            for sentiment, count in sentiment_dist.items():
                pct = count / len(new_data) * 100
                print(f"   {sentiment}: {count} ({pct:.1f}%)")
        
        return results
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        return {"error": str(e)}

def validate_deployment():
    """Validate the deployment results"""
    
    print(f"\n🔍 VALIDATING DEPLOYMENT")
    print("=" * 30)
    
    db = SupabaseDatabase()
    data = db.get_stage2_response_labeling('Rev')
    
    if data.empty:
        print(f"❌ No data found - deployment may have failed")
        return False
    
    # Validation checks
    checks = [
        ("Total records", len(data) > 0, f"{len(data)} records"),
        ("Relevance score coverage", data['relevance_score'].notna().sum() > 0, f"{data['relevance_score'].notna().sum()}/{len(data)} records"),
        ("Criteria diversity", data['criterion'].nunique() >= 5, f"{data['criterion'].nunique()} criteria"),
        ("Sentiment diversity", data['sentiment'].nunique() >= 3, f"{data['sentiment'].nunique()} sentiments"),
        ("Confidence diversity", data['confidence'].nunique() >= 2, f"{data['confidence'].nunique()} confidence levels")
    ]
    
    all_passed = True
    for check_name, passed, details in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}: {details}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 DEPLOYMENT VALIDATION SUCCESSFUL!")
    else:
        print(f"\n⚠️  DEPLOYMENT VALIDATION FAILED - Some checks failed")
    
    return all_passed

if __name__ == "__main__":
    # Deploy the system
    results = deploy_redesigned_system()
    
    if 'error' not in results:
        # Validate the deployment
        validation_success = validate_deployment()
        
        if validation_success:
            print(f"\n🚀 REDESIGNED STAGE 2 SYSTEM SUCCESSFULLY DEPLOYED!")
            print(f"   The system is now ready for competitive intelligence analysis")
        else:
            print(f"\n⚠️  Deployment completed but validation failed")
    else:
        print(f"\n❌ Deployment failed: {results['error']}") 