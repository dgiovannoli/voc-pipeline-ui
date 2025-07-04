# VOC Database Guide

## 🏗️ Database Structure

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    responses    │    │ analysis_results │    │ response_labels │    │ quality_metrics │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤    ├─────────────────┤
│ response_id (PK)│◄───┤ response_id (FK) │    │ response_id (FK)│    │ response_id (FK)│
│ verbatim_response│    │ analysis_type    │    │ label_type      │    │ metric_type     │
│ subject         │    │ analysis_text    │    │ label_value     │    │ metric_value    │
│ question        │    │ model_version    │    │ confidence_score│    │ metric_details  │
│ deal_status     │    │ confidence_score │    │ labeled_by      │    │ evaluated_at    │
│ company         │    │ analyzed_at      │    │ labeled_at      │    └─────────────────┘
│ interviewee_name│    └──────────────────┘    └─────────────────┘
│ date_of_interview│
│ created_at      │
│ updated_at      │
└─────────────────┘
```

## 🎯 How It Works

### 1. **Core Data (responses table)**
- This is your "source of truth" - the raw customer quotes
- Never gets modified once saved
- Contains basic metadata (company, interviewee, date, etc.)

### 2. **AI Analysis (analysis_results table)**
- Stores all the AI-generated insights
- Each response can have multiple analysis results
- Examples: findings, value_realization, implementation_experience

### 3. **Manual Labels (response_labels table)**
- You can add any type of label to responses
- Examples: sentiment (positive/negative), priority (high/medium/low), actionable (yes/no)
- Each label has a confidence score

### 4. **Quality Tracking (quality_metrics table)**
- Track the quality of your responses
- Examples: word_count, quality_score, validation_status

## 🚀 How to Use It

### **Option 1: Streamlit UI (Easiest)**

1. **Open your app**: `streamlit run app.py`
2. **Go to Database tab**
3. **Migrate data**: Click "Migrate Validated Quotes" or "Migrate Response Table"
4. **Filter data**: Use dropdowns to filter by company, deal status, etc.
5. **Add labels**: Select a response, choose label type, enter value, click "Add Label"
6. **Export**: Click "Export to CSV" to download filtered data

### **Option 2: Python Code (More Control)**

```python
from database import VOCDatabase

# Initialize database
db = VOCDatabase()

# Save a response
response_data = {
    'response_id': 'my_response_001',
    'verbatim_response': 'Customer quote here...',
    'subject': 'Product Features',
    'question': 'What did you think?',
    'deal_status': 'closed_won',
    'company': 'MyCompany',
    'interviewee_name': 'John Doe',
    'date_of_interview': '2024-01-15'
}
db.save_response(response_data)

# Get all responses
all_responses = db.get_responses()

# Filter by company
company_responses = db.get_responses({'company': 'MyCompany'})

# Add a label
db.add_label('my_response_001', 'sentiment', 'positive', 0.9)

# Get statistics
stats = db.get_stats()
print(f"Total responses: {stats['total_responses']}")
```

## 📊 Common Operations

### **Viewing Data**
```python
# Get all responses
responses = db.get_responses()

# Get specific response with all its data
response = db.get_response_by_id('response_001')
print(f"Response: {response['verbatim_response']}")
print(f"Analyses: {response['analyses']}")
print(f"Labels: {response['labels']}")
```

### **Filtering Data**
```python
# Filter by company
techcorp_responses = db.get_responses({'company': 'TechCorp'})

# Filter by deal status
won_deals = db.get_responses({'deal_status': 'closed_won'})

# Filter by multiple criteria
filters = {
    'company': 'TechCorp',
    'deal_status': 'closed_won'
}
filtered = db.get_responses(filters)
```

### **Adding Labels**
```python
# Add sentiment label
db.add_label('response_001', 'sentiment', 'positive', 0.9)

# Add priority label
db.add_label('response_001', 'priority', 'high', 0.8)

# Add custom label
db.add_label('response_001', 'actionable', 'yes', 0.95)
```

### **Quality Tracking**
```python
# Add word count
db.add_quality_metric('response_001', 'word_count', 150.0)

# Add quality score
db.add_quality_metric('response_001', 'quality_score', 0.85, 
                     {'details': 'Good response length and content'})
```

### **Exporting Data**
```python
# Export all data
db.export_to_csv('all_responses.csv')

# Export filtered data
db.export_to_csv('techcorp_responses.csv', {'company': 'TechCorp'})
```

## 🔍 Database Statistics

```python
stats = db.get_stats()
print(f"Total responses: {stats['total_responses']}")
print(f"Total analyses: {stats['total_analyses']}")
print(f"Total labels: {stats['total_labels']}")
print(f"Companies: {list(stats['responses_by_company'].keys())}")
print(f"Deal statuses: {list(stats['responses_by_status'].keys())}")
```

## 💡 Pro Tips

1. **Start with Streamlit**: Use the UI to get familiar with the database
2. **Migrate existing data**: Import your CSV files to populate the database
3. **Add labels gradually**: Start with simple labels like sentiment
4. **Use filters**: Find specific responses quickly with filters
5. **Export regularly**: Download filtered data for analysis in other tools

## 🆘 Troubleshooting

**Q: Where is the database file stored?**
A: It's stored as `voc_pipeline.db` in your project directory

**Q: Can I lose data?**
A: No! The database is persistent and your CSV files remain unchanged

**Q: How do I backup the database?**
A: Simply copy the `voc_pipeline.db` file to a safe location

**Q: Can I use multiple databases?**
A: Yes! Pass a different filename to `VOCDatabase("my_database.db")` 