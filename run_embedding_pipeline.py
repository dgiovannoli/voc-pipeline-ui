#!/usr/bin/env python3

"""
Complete Embedding Pipeline Runner

This script runs the complete embedding pipeline including:
1. Backfill embeddings for all existing data
2. Run Stage 4B with vector-based semantic deduplication
3. Generate summary reports
"""

import os
import sys
import logging
from datetime import datetime
from embedding_utils import EmbeddingManager
from stage4b_scorecard_analyzer import Stage4BScorecardAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'embedding_pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_complete_embedding_pipeline(client_id: str = 'default'):
    """Run the complete embedding pipeline"""
    
    logger.info("🚀 STARTING COMPLETE EMBEDDING PIPELINE")
    logger.info("=" * 60)
    logger.info(f"Client ID: {client_id}")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("=" * 60)
    
    # Step 1: Initialize embedding manager
    logger.info("\n📦 Step 1: Initializing Embedding Manager")
    try:
        embedding_manager = EmbeddingManager()
        logger.info("✅ Embedding manager initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize embedding manager: {e}")
        return {"status": "error", "message": f"Initialization failed: {e}"}
    
    # Step 2: Backfill embeddings for all tables
    logger.info("\n🔄 Step 2: Backfilling Embeddings for All Tables")
    try:
        backfill_result = embedding_manager.backfill_all_embeddings(client_id)
        logger.info(f"✅ Backfill completed: {backfill_result}")
    except Exception as e:
        logger.error(f"❌ Backfill failed: {e}")
        return {"status": "error", "message": f"Backfill failed: {e}"}
    
    # Step 3: Run Stage 4B with vector-based semantic deduplication
    logger.info("\n🎯 Step 3: Running Stage 4B with Vector-Based Semantic Deduplication")
    try:
        analyzer = Stage4BScorecardAnalyzer()
        stage4b_result = analyzer.process_scorecard_themes(client_id)
        logger.info(f"✅ Stage 4B completed: {stage4b_result}")
    except Exception as e:
        logger.error(f"❌ Stage 4B failed: {e}")
        return {"status": "error", "message": f"Stage 4B failed: {e}"}
    
    # Step 4: Generate summary report
    logger.info("\n📊 Step 4: Generating Summary Report")
    summary = {
        "timestamp": datetime.now().isoformat(),
        "client_id": client_id,
        "backfill_results": backfill_result,
        "stage4b_results": stage4b_result,
        "total_embeddings_generated": backfill_result.get("total_updated", 0),
        "themes_generated": stage4b_result.get("themes_generated", 0),
        "themes_after_merging": stage4b_result.get("themes_after_merging", 0),
        "reduction_percentage": 0
    }
    
    if summary["themes_generated"] > 0:
        summary["reduction_percentage"] = round(
            ((summary["themes_generated"] - summary["themes_after_merging"]) / summary["themes_generated"]) * 100, 1
        )
    
    # Print summary
    logger.info("\n🎉 PIPELINE COMPLETE - SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Embeddings Generated: {summary['total_embeddings_generated']}")
    logger.info(f"Themes Generated: {summary['themes_generated']}")
    logger.info(f"Themes After Merging: {summary['themes_after_merging']}")
    logger.info(f"Reduction: {summary['reduction_percentage']}%")
    logger.info(f"Status: {summary.get('status', 'success')}")
    logger.info("=" * 60)
    
    return summary

def run_embedding_backfill_only(client_id: str = 'default'):
    """Run only the embedding backfill"""
    logger.info(f"🔄 Running embedding backfill for client {client_id}")
    
    try:
        embedding_manager = EmbeddingManager()
        result = embedding_manager.backfill_all_embeddings(client_id)
        logger.info(f"✅ Backfill completed: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Backfill failed: {e}")
        return {"status": "error", "message": str(e)}

def run_stage4b_only(client_id: str = 'default'):
    """Run only Stage 4B with existing embeddings"""
    logger.info(f"🎯 Running Stage 4B for client {client_id}")
    
    try:
        analyzer = Stage4BScorecardAnalyzer()
        result = analyzer.process_scorecard_themes(client_id)
        logger.info(f"✅ Stage 4B completed: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Stage 4B failed: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the complete embedding pipeline")
    parser.add_argument("--client-id", default="default", help="Client ID to process")
    parser.add_argument("--backfill-only", action="store_true", help="Run only embedding backfill")
    parser.add_argument("--stage4b-only", action="store_true", help="Run only Stage 4B")
    
    args = parser.parse_args()
    
    if args.backfill_only:
        result = run_embedding_backfill_only(args.client_id)
    elif args.stage4b_only:
        result = run_stage4b_only(args.client_id)
    else:
        result = run_complete_embedding_pipeline(args.client_id)
    
    print(f"\nFinal result: {result}") 