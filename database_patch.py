"""
Database Patch for Timestamp Support
Shows exactly what to add to your existing save_core_response function.
"""

# ADD THESE TWO LINES to your existing save_core_response function in supabase_database.py
# Add them after the 'created_at' line and before the harmonized subject fields section:

# ADD THESE LINES:
'start_timestamp': response_data.get('start_timestamp'),
'end_timestamp': response_data.get('end_timestamp'),

# Your updated data dictionary should look like this:
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

print("Database patch ready!")
print("To apply:")
print("1. Open supabase_database.py")
print("2. Find the save_core_response function")
print("3. Add the two timestamp lines to the data dictionary")
print("4. Save the file")
