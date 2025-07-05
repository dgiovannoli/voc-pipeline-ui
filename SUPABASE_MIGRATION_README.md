# Supabase Migration Guide

## Overview

The VOC Pipeline has been migrated from a hybrid SQLite + Supabase architecture to a **Supabase-only** architecture. This simplifies the codebase, eliminates sync issues, and provides a more robust cloud-first solution.

## What Changed

### ✅ **Removed**
- All SQLite database operations
- Hybrid database manager (`supabase_integration.py`)
- SQLite schema management
- Sync status tracking
- Local database files (`voc_pipeline.db`)

### ✅ **Added**
- Pure Supabase database manager (`supabase_database.py`)
- Direct Supabase operations for all data access
- Simplified data flow (no sync required)
- Cloud-first architecture

## Migration Steps

### 1. **Install Supabase Dependency**
```bash
pip install supabase>=2.0.0
```

### 2. **Configure Environment Variables**
Ensure your `.env` file contains:
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
```

### 3. **Run Migration Script** (if you have existing SQLite data)
```bash
python migrate_to_supabase.py
```

This script will:
- Check for existing SQLite data
- Migrate all data to Supabase
- Verify the migration
- Clean up SQLite files

### 4. **Start the Application**
```bash
streamlit run app.py
```

## New Architecture

### Database Operations
All database operations now go directly to Supabase:

```python
from supabase_database import SupabaseDatabase

# Initialize database
db = SupabaseDatabase()

# Save core response
db.save_core_response(response_data)

# Get core responses
responses = db.get_core_responses()

# Get quote analysis
analysis = db.get_quote_analysis()

# Get summary statistics
summary = db.get_summary_statistics()
```

### Key Benefits

1. **No Sync Issues**: All data is stored directly in Supabase
2. **Simplified Codebase**: Removed complex hybrid logic
3. **Better Performance**: No local database overhead
4. **Cloud-First**: Access data from anywhere
5. **Automatic Backups**: Supabase handles data persistence

## File Changes

### New Files
- `supabase_database.py` - Pure Supabase database manager
- `migrate_to_supabase.py` - Migration script
- `SUPABASE_MIGRATION_README.md` - This file

### Modified Files
- `app.py` - Updated to use Supabase only
- `enhanced_stage2_analyzer.py` - Updated to use Supabase
- `requirements.txt` - Added supabase dependency

### Removed Files (after migration)
- `database.py` - SQLite database manager
- `supabase_integration.py` - Hybrid database manager
- `update_database_schema.py` - SQLite schema updates
- `db_explorer.py` - SQLite explorer
- `production_fix.py` - SQLite fixes
- `voc_pipeline.db` - SQLite database file

## Troubleshooting

### Connection Issues
If you see "Supabase not connected" errors:

1. **Check Environment Variables**
   ```bash
   echo $SUPABASE_URL
   echo $SUPABASE_ANON_KEY
   ```

2. **Verify Supabase Project**
   - Ensure your Supabase project is active
   - Check that tables exist in your Supabase dashboard

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Data Migration Issues
If migration fails:

1. **Check Supabase Permissions**
   - Ensure your anon key has insert/select permissions
   - Verify RLS policies allow your operations

2. **Manual Migration**
   - Export SQLite data to CSV
   - Import manually through Supabase dashboard

3. **Rollback**
   - Keep your `voc_pipeline.db` file as backup
   - Migration script won't delete it until verification passes

## Support

If you encounter issues:

1. Check the Supabase dashboard for table structure
2. Verify your environment variables
3. Check the application logs for detailed error messages
4. Ensure your Supabase project has the required tables:
   - `core_responses`
   - `quote_analysis`
   - `processing_metadata`

## Next Steps

After successful migration:

1. **Test the Application**: Upload and process some files
2. **Verify Data**: Check that data appears in Supabase dashboard
3. **Clean Up**: Remove old SQLite files (if migration script didn't)
4. **Update Documentation**: Update any internal documentation

---

**Note**: This migration is designed to be safe and reversible. Your original SQLite data will be preserved until you explicitly clean it up. 