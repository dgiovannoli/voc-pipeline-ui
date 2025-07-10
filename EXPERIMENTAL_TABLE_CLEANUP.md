# 🗄️ Experimental Table Cleanup Plan

## 📊 Analysis Results

### Core Pipeline (Stages 1-4) - KEEP
- ✅ **stage1_data_responses** - Essential for data ingestion
- ✅ **stage3_findings** - Essential for findings generation
- ✅ **themes** - Essential for theme generation

### Experimental/Legacy Tables - REMOVE
- ⚠️ **scorecard_themes** - Stage 4B experimental feature
- ⚠️ **executive_themes** - Stage 5 (not in core pipeline)
- ⚠️ **criteria_scorecard** - Stage 5 (not in core pipeline)
- ⚠️ **stage2_response_labeling** - Stage 2 (not used in current core pipeline)

## 🎯 Phase 3: Database Cleanup (Updated)

### Step 1: Remove Unused Columns (Already Identified)
```sql
-- Remove unused columns from themes table
ALTER TABLE themes DROP COLUMN IF EXISTS fuzzy_match_score;
ALTER TABLE themes DROP COLUMN IF EXISTS semantic_group_id;
ALTER TABLE themes DROP COLUMN IF EXISTS scorecard_theme_id;
ALTER TABLE themes DROP COLUMN IF EXISTS synthesis_theme_id;

-- Remove unused columns from stage3_findings table
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS scorecard_criterion_priority;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS sentiment_alignment_score;
```

### Step 2: Remove Experimental Tables
```sql
-- Remove experimental tables (after verification)
DROP TABLE IF EXISTS scorecard_themes;
DROP TABLE IF EXISTS executive_themes;
DROP TABLE IF EXISTS criteria_scorecard;
DROP TABLE IF EXISTS stage2_response_labeling;
```

## 🔍 Verification Before Removal

### Check UI References
```bash
# Search for references to experimental tables in UI
grep -r "scorecard_themes" app.py
grep -r "executive_themes" app.py
grep -r "criteria_scorecard" app.py
grep -r "stage2_response_labeling" app.py
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
- **Remove 4 experimental tables**
- **Remove 6 unused columns**
- **Simplify schema** to core pipeline only
- **Improve performance** with fewer tables

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
rm import_scorecard_themes.py
```

## 💡 Benefits

### Immediate:
- **Cleaner database schema**
- **Faster queries** (fewer tables)
- **Simpler maintenance**
- **Reduced complexity**

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
6. **Test core pipeline** one final time

---

**Status:** Ready for Phase 3 database cleanup  
**Risk Level:** Low (after verification)  
**Expected Impact:** Significant database simplification 