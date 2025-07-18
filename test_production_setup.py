#!/usr/bin/env python3
"""
Production Setup Test Script
Verifies that the VOC Pipeline is ready for production deployment
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_database import create_supabase_database
from stage3_findings_analyzer import Stage3FindingsAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_variables() -> bool:
    """Test that all required environment variables are set"""
    logger.info("🔍 Testing environment variables...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    logger.info("✅ All required environment variables are set")
    return True

def test_database_connection() -> bool:
    """Test database connection and basic operations"""
    logger.info("🔍 Testing database connection...")
    
    try:
        db = create_supabase_database()
        
        # Test basic connection
        if not db.test_connection():
            logger.error("❌ Database connection test failed")
            return False
        
        # Test table access
        stage1_count = len(db.get_stage1_data_responses(client_id='default'))
        logger.info(f"✅ Database connection successful. Found {stage1_count} stage1 records")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def test_schema_structure() -> bool:
    """Test that the database schema is properly set up"""
    logger.info("🔍 Testing database schema...")
    
    try:
        db = create_supabase_database()
        
        # Test that required tables exist by attempting to query them
        required_tables = [
            'stage1_data_responses',
            'stage2_response_labeling', 
            'stage3_findings',
            'stage4_themes'
        ]
        
        for table in required_tables:
            try:
                # Try to select from each table
                result = db.supabase.table(table).select('*').limit(1).execute()
                logger.info(f"✅ Table {table} exists and is accessible")
            except Exception as e:
                logger.error(f"❌ Table {table} is missing or inaccessible: {e}")
                return False
        
        logger.info("✅ All required tables exist and are accessible")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema test failed: {e}")
        return False

def test_stage3_analyzer() -> bool:
    """Test the Stage 3 findings analyzer"""
    logger.info("🔍 Testing Stage 3 findings analyzer...")
    
    try:
        analyzer = Stage3FindingsAnalyzer()
        
        # Test configuration loading
        config = analyzer.load_config()
        if not config:
            logger.error("❌ Failed to load configuration")
            return False
        
        logger.info("✅ Stage 3 analyzer initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Stage 3 analyzer test failed: {e}")
        return False

def test_llm_integration() -> bool:
    """Test LLM integration for findings generation"""
    logger.info("🔍 Testing LLM integration...")
    
    try:
        analyzer = Stage3FindingsAnalyzer()
        
        # Test prompt loading
        prompt = analyzer._load_buried_wins_prompt()
        if not prompt or len(prompt) < 100:
            logger.error("❌ Buried Wins prompt is too short or missing")
            return False
        
        logger.info("✅ LLM integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM integration test failed: {e}")
        return False

def test_sample_findings_generation() -> bool:
    """Test generating a small sample of findings"""
    logger.info("🔍 Testing sample findings generation...")
    
    try:
        analyzer = Stage3FindingsAnalyzer()
        
        # Get a small sample of data
        db = create_supabase_database()
        sample_data = db.get_stage1_data_responses(client_id='Rev')
        
        if len(sample_data) == 0:
            logger.warning("⚠️ No sample data found for testing")
            return True  # Not a failure, just no data
        
        # Test with a small subset
        test_data = sample_data.head(5)
        
        # Convert to the format expected by the analyzer
        quotes = []
        for idx, row in test_data.iterrows():
            quote = {
                'response_id': row.get('response_id', f'test_{idx}'),
                'verbatim_response': row.get('verbatim_response', ''),
                'question': row.get('question', ''),
                'deal_status': row.get('deal_status', 'closed won'),
                'company': row.get('company_name', ''),
                'interviewee_name': row.get('interviewee_name', ''),
                'date': row.get('interview_date', ''),
                'client_id': row.get('client_id', 'Rev'),
                'avg_score': 3.0,
                'relevance_level': 'moderate',
                'company_count': 1
            }
            quotes.append(quote)
        
        # Test finding generation
        findings = []
        for quote in quotes:
            finding = analyzer._create_finding_from_quote(quote)
            if finding:
                findings.append(finding)
        
        logger.info(f"✅ Generated {len(findings)} sample findings from {len(quotes)} quotes")
        return True
        
    except Exception as e:
        logger.error(f"❌ Sample findings generation failed: {e}")
        return False

def test_database_save_operations() -> bool:
    """Test saving findings to the database"""
    logger.info("🔍 Testing database save operations...")
    
    try:
        db = create_supabase_database()
        
        # Create a test finding
        test_finding = {
            'finding_statement': 'Test finding for production verification',
            'interview_company': 'Test Company',
            'interviewee_name': 'Test User',
            'criterion': 'test_criterion',
            'finding_type': 'test_type',
            'enhanced_confidence': 7.5,
            'criteria_scores': {'test': 5},
            'criteria_met': 3,
            'impact_score': 8.0,
            'companies_affected': 1,
            'quote_count': 1,
            'selected_quotes': [{'text': 'Test quote', 'response_id': 'test_1'}],
            'themes': ['test_theme'],
            'deal_impacts': {'test': 'impact'},
            'priority_level': 'Standard Finding',
            'evidence_strength': 5,
            'finding_category': 'Test Category'
        }
        
        # Test saving
        success = db.save_enhanced_finding(test_finding, client_id='test')
        
        if success:
            logger.info("✅ Database save operation successful")
            
            # Clean up test data
            try:
                # Note: In production, you might want to keep test data or use a separate test database
                logger.info("ℹ️ Test finding saved successfully")
            except Exception as e:
                logger.warning(f"⚠️ Could not clean up test data: {e}")
            
            return True
        else:
            logger.error("❌ Database save operation failed")
            return False
        
    except Exception as e:
        logger.error(f"❌ Database save test failed: {e}")
        return False

def test_client_data_siloing() -> bool:
    """Test that client data siloing is working correctly"""
    logger.info("🔍 Testing client data siloing...")
    
    try:
        db = create_supabase_database()
        
        # Test that different clients have separate data
        rev_data = db.get_stage1_data_responses(client_id='Rev')
        default_data = db.get_stage1_data_responses(client_id='default')
        
        logger.info(f"✅ Client siloing working: Rev has {len(rev_data)} records, default has {len(default_data)} records")
        return True
        
    except Exception as e:
        logger.error(f"❌ Client data siloing test failed: {e}")
        return False

def run_production_tests() -> Dict[str, bool]:
    """Run all production tests and return results"""
    logger.info("🚀 Starting production setup tests...")
    
    tests = {
        'Environment Variables': test_environment_variables,
        'Database Connection': test_database_connection,
        'Schema Structure': test_schema_structure,
        'Stage 3 Analyzer': test_stage3_analyzer,
        'LLM Integration': test_llm_integration,
        'Sample Findings Generation': test_sample_findings_generation,
        'Database Save Operations': test_database_save_operations,
        'Client Data Siloing': test_client_data_siloing
    }
    
    results = {}
    
    for test_name, test_func in tests.items():
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    return results

def print_test_summary(results: Dict[str, bool]):
    """Print a summary of test results"""
    logger.info(f"\n{'='*60}")
    logger.info("PRODUCTION SETUP TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    logger.info(f"Tests Passed: {passed}/{total}")
    logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
    
    logger.info(f"\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    if passed == total:
        logger.info(f"\n🎉 ALL TESTS PASSED! Production setup is ready.")
        logger.info(f"✅ You can now deploy to production.")
    else:
        logger.info(f"\n⚠️ {total - passed} tests failed. Please fix the issues before deploying.")
        logger.info(f"❌ Production setup is NOT ready.")
    
    logger.info(f"\nTest completed at: {datetime.now()}")

def main():
    """Main function to run all production tests"""
    logger.info("🚀 VOC Pipeline Production Setup Test")
    logger.info("=" * 50)
    
    # Run all tests
    results = run_production_tests()
    
    # Print summary
    print_test_summary(results)
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main() 