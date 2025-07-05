#!/usr/bin/env python3

import argparse
import sys
from enhanced_stage2_analyzer import DatabaseStage2Analyzer

def main():
    parser = argparse.ArgumentParser(description='Run Stage 2 Quote Analysis')
    parser.add_argument('--force', action='store_true', 
                       help='Force reprocess all quotes (not just new ones)')
    parser.add_argument('--db', default='voc_pipeline.db', 
                       help='Database path (default: voc_pipeline.db)')
    parser.add_argument('--config', default='config/analysis_config.yaml',
                       help='Config file path (default: config/analysis_config.yaml)')
    parser.add_argument('--trends', action='store_true',
                       help='Show trend analysis after processing')
    parser.add_argument('--company', help='Filter trends by company')
    parser.add_argument('--months', type=int, default=6,
                       help='Number of months for trend analysis (default: 6)')
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = DatabaseStage2Analyzer(args.db, args.config)
        
        # Run analysis
        print("🚀 Starting Stage 2 Quote Analysis...")
        result = analyzer.process_incremental(args.force)
        
        if result.get('status') == 'success':
            print(f"\n✅ Analysis completed successfully!")
            print(f"📊 Quotes processed: {result['quotes_processed']}")
            print(f"📊 Quotes analyzed: {result['quotes_analyzed']}")
            print(f"⏱️ Processing time: {result['processing_duration_seconds']:.1f}s")
            
            # Show trends if requested
            if args.trends:
                print(f"\n📈 TREND ANALYSIS (Last {args.months} months):")
                print("=" * 50)
                
                trend_data = analyzer.get_trend_data(
                    company=args.company, 
                    months=args.months
                )
                
                if not trend_data.empty:
                    for _, row in trend_data.iterrows():
                        print(f"{row['company']} - {row['criterion']}: {row['avg_score']:.2f} ({row['quote_count']} quotes)")
                else:
                    print("No trend data available")
            
            # Show summary
            summary = result['summary']
            print(f"\n📊 SUMMARY:")
            print(f"Total quotes: {summary['total_quotes']}")
            print(f"Coverage: {summary['coverage_percentage']}%")
            print(f"Top performing criteria:")
            
            sorted_criteria = sorted(
                summary['criteria_performance'].items(),
                key=lambda x: x[1]['average_score'],
                reverse=True
            )[:5]
            
            for criterion, perf in sorted_criteria:
                print(f"  {criterion}: {perf['average_score']:.2f} ({perf['mention_count']} mentions)")
        
        elif result.get('status') == 'no_quotes_to_process':
            print("✅ No quotes to process - all quotes already analyzed")
        
        else:
            print(f"❌ Analysis failed: {result}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 