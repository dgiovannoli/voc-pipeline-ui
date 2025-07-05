#!/usr/bin/env python3
"""
Simple test script to verify batch_table.py works correctly
"""
import os
import subprocess
import sys

def test_batch_table():
    # Create a simple test transcript
    test_transcript = """
    Interviewer: Hi, can you tell us about your experience with our product?
    
    Customer: Sure! We've been using it for about 6 months now and it's been great. 
    The implementation was smooth and the team was very helpful.
    
    Interviewer: What specific benefits have you seen?
    
    Customer: We've saved about 40% on processing time and our team is much more efficient.
    The ROI has been excellent.
    """
    
    # Write test transcript to file
    with open("test_transcript.txt", "w", encoding="utf-8") as f:
        f.write(test_transcript)
    
    try:
        # Test the batch_table.py script
        result = subprocess.run([
            sys.executable, "batch_table.py",
            "--transcript", "test_transcript.txt",
            "--client", "Test Client",
            "--company", "Test Company",
            "--interviewee", "Test Customer",
            "--deal-status", "closed_won",
            "--date", "2025/01/15",
            "--output", "test_output.csv"
        ], capture_output=True, text=True, check=True)
        
        print("✅ batch_table.py test successful!")
        print("Output:", result.stdout)
        
        # Check if output file was created
        if os.path.exists("test_output.csv"):
            print("✅ Output file created successfully")
            with open("test_output.csv", "r") as f:
                content = f.read()
                print("File content preview:")
                print(content[:500])
        else:
            print("❌ Output file not created")
            
    except subprocess.CalledProcessError as e:
        print("❌ batch_table.py test failed!")
        print("Error:", e.stderr)
        return False
    except Exception as e:
        print("❌ Unexpected error:", e)
        return False
    finally:
        # Clean up test files
        for file in ["test_transcript.txt", "test_output.csv"]:
            if os.path.exists(file):
                os.remove(file)
    
    return True

if __name__ == "__main__":
    test_batch_table() 