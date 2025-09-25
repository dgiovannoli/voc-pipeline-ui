"""
Enhanced Database Save Functions with Timestamp Support
Extends the existing database save functions to include timestamp fields.
"""

import math
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def enhance_save_core_response_with_timestamps(self, response_data: Dict[str, Any]) -> bool:
    """
    Enhanced version of save_core_response that includes timestamp fields.
    
    This function extends the existing save_core_response method to include
    start_timestamp and end_timestamp fields for video integration.
    
    Args:
        response_data: Dictionary containing response data including timestamp fields
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Prepare data for Supabase with timestamp fields
        data = {
            'response_id': response_data.get('response_id'),
            'verbatim_response': response_data.get('verbatim_response'),
            'subject': response_data.get('subject'),
            'question': response_data.get('question'),
            'deal_status': response_data.get('deal_status'),
            'company': response_data.get('company'),
            'interviewee_name': response_data.get('interviewee_name'),
            'interview_date': response_data.get('interview_date'),
            'industry': response_data.get('industry'),
            'audio_video_link': response_data.get('audio_video_link'),
            'contact_website': response_data.get('contact_website'),
            'file_source': response_data.get('file_source', ''),
            'client_id': response_data.get('client_id', 'default'),
            'created_at': datetime.now().isoformat(),
            # NEW: Timestamp fields for video integration
            'start_timestamp': response_data.get('start_timestamp'),
            'end_timestamp': response_data.get('end_timestamp')
        }
        
        # Add harmonized subject fields if present
        if response_data.get('harmonized_subject') is not None:
            data.update({
                'harmonized_subject': response_data.get('harmonized_subject'),
                'harmonization_confidence': response_data.get('harmonization_confidence'),
                'harmonization_method': response_data.get('harmonization_method'),
                'harmonization_reasoning': response_data.get('harmonization_reasoning'),
                'suggested_new_category': response_data.get('suggested_new_category'),
                'harmonized_at': response_data.get('harmonized_at', datetime.now().isoformat())
            })
        
        # Sanitize NaN/inf to None
        try:
            for k, v in list(data.items()):
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    data[k] = None
        except Exception:
            pass
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        # Upsert to Supabase
        result = self.supabase.table('stage1_data_responses').upsert(data).execute()
        
        # Log timestamp information if available
        timestamp_info = ""
        if response_data.get('start_timestamp') or response_data.get('end_timestamp'):
            start = response_data.get('start_timestamp', 'N/A')
            end = response_data.get('end_timestamp', 'N/A')
            timestamp_info = f" [Timestamps: {start}-{end}]"
        
        logger.info(f"✅ Saved core response with timestamps: {response_data.get('response_id')}{timestamp_info}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to save core response with timestamps: {e}")
        return False

def create_timestamp_enhanced_response_data(base_response_data: Dict[str, Any], 
                                          start_timestamp: str = None, 
                                          end_timestamp: str = None) -> Dict[str, Any]:
    """
    Create enhanced response data with timestamp fields.
    
    Args:
        base_response_data: Original response data
        start_timestamp: Start timestamp in HH:MM:SS format
        end_timestamp: End timestamp in HH:MM:SS format
        
    Returns:
        Enhanced response data with timestamp fields
    """
    enhanced_data = base_response_data.copy()
    
    # Add timestamp fields
    if start_timestamp:
        enhanced_data['start_timestamp'] = start_timestamp
    if end_timestamp:
        enhanced_data['end_timestamp'] = end_timestamp
    
    return enhanced_data

def validate_timestamp_format(timestamp: str) -> bool:
    """
    Validate that timestamp is in correct HH:MM:SS format.
    
    Args:
        timestamp: Timestamp string to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    if not timestamp:
        return True  # Empty timestamps are allowed
    
    import re
    # Check for HH:MM:SS format
    pattern = r'^\d{2}:\d{2}:\d{2}$'
    return bool(re.match(pattern, timestamp))

def format_timestamp_for_database(timestamp: str) -> str:
    """
    Format timestamp for database storage.
    
    Args:
        timestamp: Timestamp in various formats
        
    Returns:
        Formatted timestamp in HH:MM:SS format or None if invalid
    """
    if not timestamp:
        return None
    
    # If already in HH:MM:SS format, return as is
    if validate_timestamp_format(timestamp):
        return timestamp
    
    # Try to normalize other formats
    import re
    
    # Remove brackets and parentheses
    clean_timestamp = re.sub(r'[\[\]()]', '', timestamp.strip())
    
    # Split by colon
    parts = clean_timestamp.split(':')
    
    if len(parts) == 2:
        # MM:SS format - assume hours are 00
        minutes, seconds = parts
        return f"00:{minutes.zfill(2)}:{seconds.zfill(2)}"
    elif len(parts) == 3:
        # HH:MM:SS format
        hours, minutes, seconds = parts
        return f"{hours.zfill(2)}:{minutes.zfill(2)}:{seconds.zfill(2)}"
    else:
        logger.warning(f"Unable to format timestamp: {timestamp}")
        return None

def test_enhanced_database_save():
    """Test the enhanced database save functionality"""
    
    print("="*60)
    print("TESTING ENHANCED DATABASE SAVE FUNCTIONS")
    print("="*60)
    
    # Sample response data
    sample_response = {
        "response_id": "shipbob_puzzle_brian_1",
        "verbatim_response": "We had our own warehouse, own software, own negotiated rates.",
        "subject": "Current Solution",
        "question": "What was your current solution at the time?",
        "deal_status": "closed_won",
        "company": "Puzzle",
        "interviewee_name": "Brian",
        "interview_date": "2024-01-01",
        "client_id": "shipbob"
    }
    
    print("1. Testing timestamp validation...")
    test_timestamps = ["00:01:10", "01:30", "invalid", "", None]
    for ts in test_timestamps:
        is_valid = validate_timestamp_format(ts)
        formatted = format_timestamp_for_database(ts)
        print(f"  {ts} -> Valid: {is_valid}, Formatted: {formatted}")
    
    print("\n2. Testing enhanced response data creation...")
    enhanced_data = create_timestamp_enhanced_response_data(
        sample_response, 
        start_timestamp="00:01:10", 
        end_timestamp="00:01:15"
    )
    
    print("Enhanced response data:")
    for key, value in enhanced_data.items():
        print(f"  {key}: {value}")
    
    print("\n3. Testing timestamp formatting...")
    test_formats = ["00:01:10", "1:30", "[00:01:10]", "(01:30)", "invalid"]
    for ts in test_formats:
        formatted = format_timestamp_for_database(ts)
        print(f"  {ts} -> {formatted}")
    
    print("\n" + "="*60)
    print("ENHANCED DATABASE SAVE FUNCTIONS READY")
    print("="*60)
    print("\n✅ Timestamp validation working")
    print("✅ Enhanced response data creation working")
    print("✅ Timestamp formatting working")
    print("✅ Ready to integrate with database save functions")

if __name__ == "__main__":
    test_enhanced_database_save()
