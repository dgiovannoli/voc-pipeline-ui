# 🧹 Codebase Cleanup Plan

## 📊 Current State Analysis

### Files by Category:
- **Core Files (Keep):** 4-5 essential files
- **Backup/Broken Files (Remove):** ~20 files
- **Test/Debug Files (Remove):** ~50 files  
- **Unused Modules (Verify):** ~30 files
- **Configuration Files (Keep):** ~5 files

## 🎯 Phase 1: Safe Removals (No Risk)

### Backup/Broken Files to Remove:
```
app_backup.py
app_broken.py
app_clean.py
app_original.py
app_temp.py
app_nomarkdown.py
```

### Debug/Test Files to Remove:
```
debug_*.py
test_debug_*.py
stage4b_*.py
individual_components_test_*.py
enhanced_improvements_test_results_*.json
test_summary_*.json
```

### Archive Files to Remove:
```
archive/ (entire directory)
*.bak files
*.backup files
```

## 🎯 Phase 2: Verification Required

### Modules to Verify:
```
coders/ (check if used)
loaders/ (check if used)
validators/ (check if used)
prompts/ (check if used)
```

### Test Files to Verify:
```
test_*.py (except core tests)
simple_*.py
check_*.py
```

## 🎯 Phase 3: Database Cleanup

### Tables to Analyze:
- `themes` - Check for unused columns
- `stage3_findings` - Check for unused columns  
- `stage1_data_responses` - Check for unused columns
- `quote_analyses` - Check if table is used
- `scorecard_themes` - Check if table is used

### Potential Unused Columns:
- `quality_scores` (if not using enhanced scoring)
- `selected_quotes` (if not using quote attribution)
- `criteria_covered` (if not using cross-criteria)
- Various metadata fields

## 🎯 Phase 4: Configuration Cleanup

### Files to Review:
```
config/analysis_config.yaml - Remove unused settings
requirements.txt - Remove unused packages
pyproject.toml - Clean up dependencies
```

## 🔧 Implementation Strategy

### Step 1: Create Backup
```bash
git checkout -b cleanup-branch
git add .
git commit -m "Backup before cleanup"
```

### Step 2: Remove Safe Files
```bash
# Remove backup/broken files
rm app_backup.py app_broken.py app_clean.py app_original.py app_temp.py app_nomarkdown.py

# Remove debug files
rm debug_*.py
rm test_debug_*.py
rm stage4b_*.py
rm individual_components_test_*.py

# Remove test results
rm enhanced_improvements_test_results_*.json
rm test_summary_*.json
```

### Step 3: Test System
```bash
# Test core functionality
python -c "from stage3_findings_analyzer import Stage3FindingsAnalyzer; print('Stage 3 works')"
python -c "from stage4_theme_analyzer import Stage4ThemeAnalyzer; print('Stage 4 works')"
python -c "from supabase_database import SupabaseDatabase; print('Database works')"
```

### Step 4: Verify Modules
```bash
# Test each module individually
python -c "import coders; print('coders module works')"
python -c "import loaders; print('loaders module works')"
python -c "import validators; print('validators module works')"
python -c "import prompts; print('prompts module works')"
```

### Step 5: Database Analysis
```sql
-- Check for unused columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'themes';

-- Check table usage
SELECT COUNT(*) FROM themes;
SELECT COUNT(*) FROM stage3_findings;
SELECT COUNT(*) FROM stage1_data_responses;
```

## 🚨 Safety Measures

### Before Each Phase:
1. **Create git branch** for that phase
2. **Test core functionality** after each removal
3. **Keep backups** of removed files for 1 week
4. **Document what was removed** and why

### Testing Checklist:
- [ ] Stage 3 findings generation works
- [ ] Stage 4 theme generation works  
- [ ] Database connections work
- [ ] App runs without errors
- [ ] No import errors

## 📈 Expected Results

### File Reduction:
- **Before:** ~129 files
- **After:** ~40-50 files
- **Reduction:** ~60-70% fewer files

### Database Optimization:
- Remove unused columns
- Drop unused tables
- Optimize indexes

### Performance Improvement:
- Faster imports
- Cleaner codebase
- Easier maintenance

## 🎯 Success Criteria

### Phase 1 Complete:
- [ ] All backup/broken files removed
- [ ] All debug files removed
- [ ] System still works
- [ ] Git commit with changes

### Phase 2 Complete:
- [ ] Unused modules identified
- [ ] Unused modules removed or kept
- [ ] System still works
- [ ] Documentation updated

### Phase 3 Complete:
- [ ] Database schema optimized
- [ ] Unused columns removed
- [ ] Unused tables dropped
- [ ] Performance improved

### Phase 4 Complete:
- [ ] Configuration cleaned
- [ ] Dependencies optimized
- [ ] Documentation updated
- [ ] Final testing complete

## 🚀 Next Steps

1. **Start with Phase 1** (safest)
2. **Test thoroughly** after each removal
3. **Document everything** that's removed
4. **Create final cleanup report**
5. **Update documentation** for new clean structure 