# Supabase Setup Guide for VOC Pipeline

This guide walks you through setting up a hybrid SQLite + Supabase approach for your VOC pipeline.

## 🎯 Why Hybrid Approach?

**Local Development (SQLite):**
- ✅ Zero cost, fast processing
- ✅ Works offline
- ✅ Perfect for AI-heavy workloads
- ✅ Version control friendly

**Cloud Sharing (Supabase):**
- ✅ Real-time collaboration
- ✅ Web-based dashboards
- ✅ Built-in authentication
- ✅ API access for integrations

## 📋 Prerequisites

1. **Supabase Account**: Sign up at [supabase.com](https://supabase.com)
2. **Python Environment**: Your existing VOC pipeline setup
3. **API Keys**: You'll get these from Supabase dashboard

## 🚀 Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Choose your organization
4. Enter project details:
   - **Name**: `voc-pipeline-ui`
   - **Database Password**: Generate a strong password
   - **Region**: Choose closest to you
5. Click "Create new project"
6. Wait for setup to complete (2-3 minutes)

## 🗄️ Step 2: Create Database Tables

Once your project is ready, go to the **SQL Editor** in your Supabase dashboard and run these commands:

```sql
-- Core responses table (matches your SQLite schema)
CREATE TABLE stage1_data_responses (
    response_id VARCHAR PRIMARY KEY,
    verbatim_response TEXT,
    subject VARCHAR,
    question TEXT,
    deal_status VARCHAR,
    company VARCHAR,
    interviewee_name VARCHAR,
    interview_date DATE,
    file_source VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Quote analysis table
CREATE TABLE stage2_response_labeling (
    analysis_id SERIAL PRIMARY KEY,
    quote_id VARCHAR,
    criterion VARCHAR NOT NULL,
    score DECIMAL(3,2),
    priority VARCHAR CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    confidence VARCHAR CHECK (confidence IN ('high', 'medium', 'low')),
    relevance_explanation TEXT,
    deal_weighted_score DECIMAL(3,2),
    context_keywords TEXT,
    question_relevance VARCHAR CHECK (question_relevance IN ('direct', 'indirect', 'unrelated')),
    analysis_timestamp TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (quote_id) REFERENCES stage1_data_responses(response_id) ON DELETE CASCADE,
    UNIQUE(quote_id, criterion)
);

-- Processing metadata table
CREATE TABLE processing_metadata (
    metadata_id SERIAL PRIMARY KEY,
    processing_date TIMESTAMP DEFAULT NOW(),
    quotes_processed INTEGER,
    quotes_with_scores INTEGER,
    processing_errors INTEGER,
    config_version VARCHAR,
    processing_duration_seconds INTEGER
);

-- Create indexes for performance
CREATE INDEX idx_stage1_data_responses_company ON stage1_data_responses(company);
CREATE INDEX idx_stage1_data_responses_deal_status ON stage1_data_responses(deal_status);
CREATE INDEX idx_stage1_data_responses_date ON stage1_data_responses(interview_date);
CREATE INDEX idx_stage2_response_labeling_quote_id ON stage2_response_labeling(quote_id);
CREATE INDEX idx_stage2_response_labeling_criterion ON stage2_response_labeling(criterion);
```

## 🔑 Step 3: Get API Keys

1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (looks like: `https://your-project.supabase.co`)
   - **Anon/Public Key** (starts with `eyJ...`)

## 🐍 Step 4: Install Supabase Python Client

```bash
pip install supabase
```

## ⚙️ Step 5: Configure Environment Variables

Create or update your `.env` file:

```bash
# Existing variables
OPENAI_API_KEY=your_openai_key_here

# New Supabase variables
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

## 🔧 Step 6: Test the Integration

Run the test script to verify everything works:

```bash
python supabase_integration.py
```

You should see output like:
```
🔍 Hybrid Database Status:
{
  "supabase_available": true,
  "stage1_data_responses": {"local_only": 0},
  "stage2_response_labeling": {"local_only": 0},
  "total_local_responses": 0,
  "total_local_analyses": 0
}
```

## 📊 Step 7: Sync Your Existing Data

If you have existing data in SQLite, sync it to Supabase:

```python
from supabase_integration import setup_hybrid_database

# Setup hybrid database
db = setup_hybrid_database()

# Sync all local data to cloud
sync_stats = db.sync_all_to_supabase()
print(f"Synced: {sync_stats}")
```

## 🌐 Step 8: Create Web Dashboard (Optional)

You can create a simple web dashboard using Supabase's built-in features:

1. Go to **Table Editor** in Supabase dashboard
2. Select your tables to view data
3. Use **SQL Editor** for custom queries
4. Set up **Row Level Security (RLS)** if needed

## 🔄 Step 9: Update Your Streamlit App

Modify your `app.py` to use the hybrid approach:

```python
# Add to your imports
from supabase_integration import HybridDatabaseManager

# Initialize hybrid database
db_manager = HybridDatabaseManager()

# Use for data retrieval (automatically chooses best source)
def get_data_for_display(filters=None):
    return db_manager.get_data_for_sharing(filters)

# Sync after processing
def sync_after_processing():
    stats = db_manager.sync_all_to_supabase()
    st.success(f"Synced {stats['stage1_data_responses']} responses to cloud")
```

## 💰 Cost Analysis

**Supabase Free Tier:**
- 500MB database
- 2GB bandwidth
- 50,000 monthly active users
- Perfect for small to medium VOC projects

**Paid Tiers:**
- Pro: $25/month (8GB database, 250GB bandwidth)
- Team: $599/month (100GB database, 2TB bandwidth)

**Your Use Case:**
- 33 quotes = ~1-2MB of data
- Free tier will last for thousands of interviews
- No cost for local processing

## 🚨 Important Considerations

### **Data Privacy**
- Supabase is GDPR compliant
- Data is stored in your chosen region
- Consider if your VOC data can be in the cloud

### **Sync Strategy**
- **One-way sync**: Local → Cloud (recommended)
- **Manual sync**: Trigger when needed
- **Automatic sync**: After each processing batch

### **Fallback Strategy**
- App works offline with SQLite
- Falls back to local data if Supabase is unavailable
- No data loss if cloud sync fails

## 🔧 Troubleshooting

### **Connection Issues**
```bash
# Test connection
python -c "
from supabase_integration import HybridDatabaseManager
db = HybridDatabaseManager()
print('Supabase available:', bool(db.supabase))
"
```

### **Schema Mismatches**
- Ensure Supabase tables match SQLite schema
- Use the SQL commands above exactly
- Check for case sensitivity issues

### **Sync Failures**
- Check network connectivity
- Verify API keys are correct
- Look at error logs in Supabase dashboard

## 📈 Next Steps

1. **Test with small dataset** first
2. **Set up Row Level Security** if needed
3. **Create custom dashboards** in Supabase
4. **Set up automated sync** after processing
5. **Monitor usage** in Supabase dashboard

## 🎉 Benefits You'll Get

1. **Zero-cost local development** continues
2. **Real-time collaboration** for team members
3. **Web-based sharing** without local setup
4. **API access** for future integrations
5. **Automatic backups** in the cloud
6. **Scalability** as your data grows

The hybrid approach gives you the best of both worlds: fast local processing and powerful cloud sharing capabilities! 