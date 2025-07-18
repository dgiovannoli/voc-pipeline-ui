#!/usr/bin/env python3

from stage3_findings_analyzer import Stage3FindingsAnalyzer

def test_stage3_analysis():
    """Test Stage 3 analysis with client_id 'Rev'"""
    
    print("🔍 Testing Stage 3 analysis with client_id 'Rev'...")
    
    try:
        # Initialize analyzer
        analyzer = Stage3FindingsAnalyzer()
        
        # Run Stage 3 analysis with client_id "Rev"
        result = analyzer.process_stage3_findings(client_id='Rev')
        
        print(f"✅ Stage 3 analysis completed!")
        print(f"📊 Result: {result}")
        
        if result and result.get('status') == 'success':
            print(f"🎉 Successfully generated findings for client 'Rev'")
        else:
            print(f"⚠️ Analysis completed but may have issues: {result}")
            
    except Exception as e:
        print(f"❌ Stage 3 analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stage3_analysis() 