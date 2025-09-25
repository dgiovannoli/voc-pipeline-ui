"""
Database Save Function Patch
Shows how to modify the existing save_core_response function to include timestamp support.
"""

# Here's how to modify your existing save_core_response function in supabase_database.py:

def save_core_response_with_timestamps(self, response_data: Dict[str, Any]) -> bool:
    """Save a core response to Supabase with timestamp support"""
    try:
        # Prepare data for Supabase
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
            # NEW: Add these two lines for timestamp support
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
        
        # Enhanced logging with timestamp info
        timestamp_info = ""
        if response_data.get('start_timestamp') or response_data.get('end_timestamp'):
            start = response_data.get('start_timestamp', 'N/A')
            end = response_data.get('end_timestamp', 'N/A')
            timestamp_info = f" [Timestamps: {start}-{end}]"
        
        logger.info(f"✅ Saved core response: {response_data.get('response_id')}{timestamp_info}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to save core response: {e}")
        return False

# ALTERNATIVE: If you want to modify the existing function in place,
# just add these two lines to the data dictionary in your existing save_core_response function:

# ADD THESE LINES:
# 'start_timestamp': response_data.get('start_timestamp'),
# 'end_timestamp': response_data.get('end_timestamp')

# The lines should be added after the 'created_at' line and before the harmonized subject fields section.

print("Database save function patch ready!")
print("To apply:")
print("1. Open supabase_database.py")
print("2. Find the save_core_response function")
print("3. Add the two timestamp lines to the data dictionary")
print("4. Optionally enhance the logging to show timestamp information")
