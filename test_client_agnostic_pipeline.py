#!/usr/bin/env python3
"""
Test Client-Agnostic Pipeline
Demonstrates the full pipeline with client-agnostic feedback detection
"""

import logging
from supabase_database import SupabaseDatabase
from client_specific_classifier import ClientSpecificClassifier

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_client_agnostic_pipeline():
    """Test the full pipeline with client-agnostic feedback detection"""
    
    print("🧪 Testing Client-Agnostic Pipeline")
    print("=" * 50)
    
    # Test with default client (which has findings)
    client_id = "default"
    
    print(f"\n🔄 Step 1: Running client-specific classifier for {client_id}...")
    
    classifier = ClientSpecificClassifier(client_id)
    success = classifier.classify_findings()
    
    if success:
        print(f"✅ Client-specific classification completed successfully for {client_id}")
        
        # Show summary of findings
        db = SupabaseDatabase()
        findings = db.get_stage3_findings_list(client_id)
        
        print(f"\n📊 Summary for {client_id}:")
        print(f"   Total findings: {len(findings)}")
        
        # Show sample findings with their classification
        print(f"\n🔍 Sample findings:")
        for i, finding in enumerate(findings[:3]):
            print(f"   {i+1}. {finding['finding_id']}: {finding['finding_statement'][:80]}...")
            
    else:
        print(f"❌ Client-specific classification failed for {client_id}")
    
    print(f"\n🎯 Key Features of Client-Agnostic Detection:")
    print("   ✅ No manual feature lists required")
    print("   ✅ LLM infers client-specific feedback from context")
    print("   ✅ Works across different clients and industries")
    print("   ✅ Distinguishes between specific product feedback and market trends")
    print("   ✅ Uses evidence-driven classification with clear reasoning")

if __name__ == "__main__":
    test_client_agnostic_pipeline() 