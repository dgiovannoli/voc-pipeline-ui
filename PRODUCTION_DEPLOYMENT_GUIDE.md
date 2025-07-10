# Production Deployment Guide

## 🚨 The "no such column: sync_status" Error

This error occurs when the production environment is using an old database file that doesn't have the `sync_status` column. Here's how to fix it permanently.

## 🔧 Quick Fix (Recommended)

### Option 1: Use the Production Startup Script
```bash
# Make sure you're in the voc-pipeline-ui directory
cd /path/to/voc-pipeline-ui

# Activate virtual environment
source .venv/bin/activate

# Run the production startup script
./start_production.sh
```

### Option 2: Manual Fix
```bash
# 1. Stop all Streamlit processes
pkill -f streamlit

# 2. Fix the database schema
python production_fix.py

# 3. Start Streamlit in production mode
streamlit run app.py --server.port 8501 --server.headless true
```

## 📊 Verify the Fix

### Check Database Schema
```bash
python production_fix.py info
```

This should show:
- ✅ `sync_status` column in `stage1_data_responses` table
- ✅ `sync_status` column in `stage2_response_labeling` table
- ✅ Correct number of records

### Test the Supabase Sync
1. Open http://localhost:8501
2. Go to the "Supabase Sync" tab
3. The error should be gone

## 🏗️ Production Deployment Steps

### 1. Environment Setup
```bash
# Ensure you're in the correct directory
cd /path/to/voc-pipeline-ui

# Activate virtual environment
source .venv/bin/activate

# Verify environment variables
echo $OPENAI_API_KEY
```

### 2. Database Verification
```bash
# Check database status
python production_fix.py info

# Fix any schema issues
python production_fix.py
```

### 3. Start Production Server
```bash
# Use the production startup script
./start_production.sh

# Or manually:
streamlit run app.py \
    --server.port 8501 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --browser.gatherUsageStats false
```

## 🔍 Troubleshooting

### If the error persists:

1. **Check which database file is being used:**
   ```bash
   python -c "
   import os
   print('Current working directory:', os.getcwd())
   print('Database exists:', os.path.exists('voc_pipeline.db'))
   print('Database path:', os.path.abspath('voc_pipeline.db'))
   "
   ```

2. **Verify database schema:**
   ```bash
   sqlite3 voc_pipeline.db ".schema stage1_data_responses"
   ```

3. **Check for multiple database files:**
   ```bash
   find . -name "*.db" -type f
   ```

4. **Force recreate database:**
   ```bash
   # Backup current database
   cp voc_pipeline.db voc_pipeline.db.backup.$(date +%Y%m%d_%H%M%S)
   
   # Remove and recreate
   rm voc_pipeline.db
   python -c "from database import VOCDatabase; VOCDatabase()"
   ```

### Common Issues:

1. **Wrong working directory:** Make sure you're in the `voc-pipeline-ui` directory
2. **Multiple Streamlit processes:** Kill all existing processes before starting
3. **Cached database:** The app might be using a cached version
4. **Environment variables:** Ensure `OPENAI_API_KEY` is set

## 📁 File Structure

After deployment, your directory should look like:
```
voc-pipeline-ui/
├── app.py                          # Main Streamlit app
├── database.py                     # Database operations
├── enhanced_stage2_analyzer.py     # Stage 2 analysis
├── voc_pipeline.db                 # Main database (with sync_status)
├── production_fix.py               # Database fix script
├── deploy_to_production.py         # Deployment script
├── start_production.sh             # Production startup script
├── config/
│   └── analysis_config.yaml        # Analysis configuration
└── .venv/                          # Virtual environment
```

## 🚀 Production Best Practices

1. **Always use the production startup script** to ensure correct database usage
2. **Keep backups** of your database before major changes
3. **Monitor logs** for any errors
4. **Use environment variables** for sensitive configuration
5. **Regularly verify** the database schema is correct

## 📞 Support

If you continue to see the "no such column: sync_status" error:

1. Run `python production_fix.py info` to check database status
2. Check the terminal output for any error messages
3. Verify you're using the correct database file path
4. Ensure all Streamlit processes are stopped before restarting

The production fix script will automatically:
- ✅ Check database schema
- ✅ Add missing columns
- ✅ Create backups
- ✅ Verify the fix worked 