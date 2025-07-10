# 🧹 Updated Cleanup Plan

## 📊 Revised Table Analysis

### ✅ KEEP (Core Pipeline + Useful):
- **stage1_data_responses** - Stage 1 data ingestion
- **stage3_findings** - Stage 3 findings generation  
- **stage4_themes** - Stage 4 theme generation
- **stage2_response_labeling** - Stage 2 quote scoring (useful for analysis)

### 🗑️ REMOVE (Experimental/Legacy):
- **scorecard_stage4_themes** - Stage 4B experimental feature
- **executive_stage4_themes** - Stage 5 (not in core pipeline)
- **criteria_scorecard** - Stage 5 (not in core pipeline)

## 🎯 Phase 3: Database Cleanup (Updated)

### Step 1: Remove Unused Columns (Safe)
```sql
-- Remove unused columns from stage4_themes table
ALTER TABLE stage4_themes DROP COLUMN IF EXISTS fuzzy_match_score;
ALTER TABLE stage4_themes DROP COLUMN IF EXISTS semantic_group_id;
ALTER TABLE stage4_themes DROP COLUMN IF EXISTS scorecard_theme_id;
ALTER TABLE stage4_themes DROP COLUMN IF EXISTS synthesis_theme_id;

-- Remove unused columns from stage3_findings table
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS scorecard_criterion_priority;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS sentiment_alignment_score;
```

### Step 2: Remove Experimental Tables
```sql
-- Remove experimental tables (after verification)
DROP TABLE IF EXISTS scorecard_stage4_themes;
DROP TABLE IF EXISTS executive_stage4_themes;
DROP TABLE IF EXISTS criteria_scorecard;
```

### Step 3: Check and Remove Views (if any)
```sql
-- List all views
SELECT schemaname, viewname FROM pg_views WHERE schemaname = 'public';

-- Drop views if they exist (replace view_name with actual view names)
-- DROP VIEW IF EXISTS view_name;
```

## 🔍 Verification Before Removal

### Check UI References
```bash
# Search for references to experimental tables in UI
grep -r "scorecard_stage4_themes" app.py
grep -r "executive_stage4_themes" app.py
grep -r "criteria_scorecard" app.py
```

### Check Code Dependencies
```bash
# Search for imports and usage
grep -r "stage4b_scorecard_analyzer" .
grep -r "stage5_executive_analyzer" .
grep -r "scorecard_theme_ui" .
```

### Test Core Pipeline
```bash
# Test that core pipeline still works
python -c "from stage3_findings_analyzer import Stage3FindingsAnalyzer; print('Stage 3 works')"
python -c "from stage4_theme_analyzer import Stage4ThemeAnalyzer; print('Stage 4 works')"
```

## 🚨 Safety Measures

### Before Removal:
1. **Backup database** (if possible)
2. **Test core functionality** thoroughly
3. **Check UI components** for references
4. **Verify no critical features** depend on experimental tables

### After Removal:
1. **Test Stage 3** - findings generation
2. **Test Stage 4** - theme generation
3. **Test app.py** - UI functionality
4. **Verify no errors** in application

## 📈 Expected Results

### Database Optimization:
- **Remove 3 experimental tables**
- **Remove 6 unused columns**
- **Keep stage2_response_labeling** (useful for analysis)
- **Simplify schema** to core pipeline + useful tables

### Code Cleanup:
- **Remove experimental modules** (stage4b, stage5)
- **Clean up UI components** that reference experimental tables
- **Simplify codebase** to core pipeline only

## 🎯 Implementation Steps

### Step 1: Column Cleanup (Safe)
```bash
# Execute the column removal SQL in Supabase dashboard
# (Already identified in database_cleanup.sql)
```

### Step 2: Verify No Dependencies
```bash
# Check for any remaining references
python -c "import app; print('App imports work')"
```

### Step 3: Remove Experimental Tables
```bash
# Execute table removal SQL in Supabase dashboard
# (After thorough testing)
```

### Step 4: Remove Experimental Code
```bash
# Remove experimental files
rm stage4b_scorecard_analyzer.py
rm stage5_executive_analyzer.py
rm scorecard_theme_ui.py
rm import_scorecard_stage4_themes.py
```

### Step 5: Check for Views
```bash
# Check if there are any database views to remove
# (Will need to check in Supabase dashboard)
```

## 💡 Benefits

### Immediate:
- **Cleaner database schema**
- **Faster queries** (fewer tables)
- **Simpler maintenance**
- **Reduced complexity**
- **Keep useful stage2_response_labeling data**

### Long-term:
- **Focus on core pipeline**
- **Easier debugging**
- **Clearer architecture**
- **Better performance**

## 🚀 Next Steps

1. **Execute column cleanup** (already identified)
2. **Test thoroughly** after column removal
3. **Verify no dependencies** on experimental tables
4. **Remove experimental tables** if safe
5. **Remove experimental code** files
6. **Check for and remove views** if any
7. **Test core pipeline** one final time

---

**Status:** Ready for Phase 3 database cleanup  
**Risk Level:** Low (after verification)  
**Expected Impact:** Significant database simplification while keeping useful data 