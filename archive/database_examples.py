#!/usr/bin/env python3
"""
Examples of how to use the VOC Database directly in Python
"""
from database import VOCDatabase
import pandas as pd

# Initialize the database
db = VOCDatabase()

print("=== VOC Database Usage Examples ===\n")

# Example 1: Save a new response
print("1. Saving a new response...")
response_data = {
    'response_id': 'example_001',
    'verbatim_response': 'The product integration was seamless and saved us 30% time.',
    'subject': 'Product Integration',
    'question': 'How was the product integration experience?',
    'deal_status': 'closed_won',
    'company': 'TechCorp',
    'interviewee_name': 'John Smith',
    'date_of_interview': '2024-01-15',
    'findings': 'Positive integration experience with measurable time savings',
    'value_realization': '30% time savings achieved',
    'implementation_experience': 'Seamless integration process'
}

success = db.save_response(response_data)
print(f"✅ Response saved: {success}\n")

# Example 2: Get all responses
print("2. Getting all responses...")
all_responses = db.get_responses()
print(f"Found {len(all_responses)} responses")
if len(all_responses) > 0:
    print("Sample response:")
    print(f"  ID: {all_responses.iloc[0]['response_id']}")
    print(f"  Subject: {all_responses.iloc[0]['subject']}")
    print(f"  Company: {all_responses.iloc[0]['company']}")
print()

# Example 3: Filter responses by company
print("3. Filtering by company...")
techcorp_responses = db.get_responses({'company': 'TechCorp'})
print(f"Found {len(techcorp_responses)} responses from TechCorp")
print()

# Example 4: Get a specific response with all its data
print("4. Getting a specific response...")
response = db.get_response_by_id('example_001')
if response:
    print(f"Response ID: {response['response_id']}")
    print(f"Subject: {response['subject']}")
    print(f"Analyses: {len(response.get('analyses', {}))} analysis results")
    print(f"Labels: {len(response.get('labels', {}))} labels")
    print(f"Quality metrics: {len(response.get('quality_metrics', {}))} metrics")
print()

# Example 5: Add labels to a response
print("5. Adding labels...")
db.add_label('example_001', 'sentiment', 'positive', 0.9)
db.add_label('example_001', 'priority', 'high', 0.8)
db.add_label('example_001', 'actionable', 'yes', 0.95)
print("✅ Added 3 labels")
print()

# Example 6: Add quality metrics
print("6. Adding quality metrics...")
db.add_quality_metric('example_001', 'word_count', 15.0)
db.add_quality_metric('example_001', 'quality_score', 0.85, {'details': 'Good response length and content'})
print("✅ Added quality metrics")
print()

# Example 7: Get database statistics
print("7. Database statistics...")
stats = db.get_stats()
print(f"Total responses: {stats['total_responses']}")
print(f"Total analyses: {stats['total_analyses']}")
print(f"Total labels: {stats['total_labels']}")
print(f"Companies: {list(stats['responses_by_company'].keys())}")
print()

# Example 8: Export filtered data to CSV
print("8. Exporting data...")
success = db.export_to_csv('example_export.csv', {'company': 'TechCorp'})
print(f"✅ Export successful: {success}")
print()

# Example 9: Search and filter examples
print("9. Advanced filtering examples...")

# Filter by multiple criteria
filters = {
    'company': 'TechCorp',
    'deal_status': 'closed_won'
}
filtered_data = db.get_responses(filters)
print(f"TechCorp won deals: {len(filtered_data)} responses")

# Get responses from last 30 days (if you have date data)
# recent_responses = db.get_responses({'date_from': '2024-01-01'})
# print(f"Recent responses: {len(recent_responses)}")

print("\n=== Database Schema Overview ===")
print("""
The database has 4 main tables:

1. responses - Your source of truth
   - response_id (unique identifier)
   - verbatim_response (the actual customer quote)
   - subject, question, company, interviewee, etc.

2. analysis_results - AI-generated insights
   - findings, value_realization, implementation_experience, etc.
   - Each response can have multiple analysis results

3. response_labels - Manual/AI labels
   - sentiment, priority, actionable, topic, quality
   - You can add any type of label you want

4. quality_metrics - Quality tracking
   - word_count, quality_score, validation_status, etc.
   - Track the quality of your responses

All tables are linked by response_id, so you can:
- Get a response and all its analyses, labels, and metrics
- Filter responses and see all related data
- Add labels and metrics to any response
- Export filtered data for analysis
""")

print("\n=== Common Use Cases ===")
print("""
1. **Data Migration**: Import existing CSV data into the database
2. **Quality Analysis**: Add quality metrics and track response quality
3. **Labeling**: Add sentiment, priority, or custom labels to responses
4. **Filtering**: Find responses by company, deal status, or other criteria
5. **Export**: Export filtered data for further analysis
6. **Analytics**: Get statistics and insights from your data
""") 