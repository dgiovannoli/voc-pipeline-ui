# VOC Pipeline Validation System

This comprehensive validation system prevents the issues we encountered with ShipBob by catching problems early and auto-fixing common issues.

## 🚀 Quick Start

### **For New Client Processing:**
```bash
# 1. Validate everything before starting
python scripts/validate_pipeline.py --client "NewClient" --csv "interviews.csv"

# 2. If validation passes, proceed with processing
# If validation fails, fix issues first
```

### **For Existing Client Issues:**
```bash
# Check data quality
python scripts/data_quality_dashboard.py --client "ExistingClient"

# Check theme limits
python scripts/theme_limiter.py --client "ExistingClient"

# Validate database schema
python scripts/database_validator.py --client "ExistingClient"
```

## 📋 Scripts Overview

### **1. CSV Validator (`csv_validator.py`)**
**What it does:** Validates CSV uploads and auto-fixes common issues
**When to use:** Before uploading any new CSV file
**Auto-fixes:**
- Column name mismatches (e.g., "Contact ID" → "Interview Contact Full Name")
- Missing required columns with smart defaults
- Extracts company names from transcripts
- Handles encoding issues

**Usage:**
```bash
python scripts/csv_validator.py "interviews.csv"
```

**Output:** Creates `interviews_VALIDATED.csv` ready for processing

### **2. Database Validator (`database_validator.py`)**
**What it does:** Checks database schema, constraints, and data integrity
**When to use:** Before running any pipeline stages
**Checks:**
- All required tables exist
- Required columns are present
- Constraints are properly configured
- Data linking between tables

**Usage:**
```bash
python scripts/database_validator.py --client "ClientName"
```

### **3. Theme Limiter (`theme_limiter.py`)**
**What it does:** Enforces strict limits on theme generation
**When to use:** After theme generation to prevent overwhelming outputs
**Limits:**
- Max 5 themes per interview
- Max 100 total interview themes
- Quality thresholds for discovered themes

**Usage:**
```bash
# Check current limits
python scripts/theme_limiter.py --client "ClientName"

# Enforce limits (trim excess themes)
python scripts/theme_limiter.py --client "ClientName" --enforce
```

### **4. Data Quality Dashboard (`data_quality_dashboard.py`)**
**What it does:** Comprehensive monitoring of data quality across all stages
**When to use:** After each processing stage to catch issues early
**Monitors:**
- Data completeness
- Data consistency
- Processing status
- Quality metrics

**Usage:**
```bash
python scripts/data_quality_dashboard.py --client "ClientName"
```

### **5. Master Validator (`validate_pipeline.py`)**
**What it does:** Runs ALL validation checks in sequence
**When to use:** Before starting any new client processing
**Complete validation:**
- CSV validation and auto-fix
- Database schema validation
- Theme limits check
- Data quality assessment

**Usage:**
```bash
python scripts/validate_pipeline.py --client "NewClient" --csv "interviews.csv"
```

## 🔄 **New Client Processing Workflow**

### **Step 1: Pre-Processing Validation**
```bash
# Run complete validation
python scripts/validate_pipeline.py --client "NewClient" --csv "interviews.csv" --output "validation_report.txt"
```

**What this catches:**
- ❌ Missing CSV columns
- ❌ Database schema issues
- ❌ Constraint problems
- ❌ Data quality issues

**What this auto-fixes:**
- ✅ Column name mismatches
- ✅ Missing required columns
- ✅ Encoding issues
- ✅ Company name extraction

### **Step 2: Process Only If Validation Passes**
If validation passes, you'll get:
- ✅ Validated CSV file ready for processing
- ✅ Database confirmed ready
- ✅ All systems go

If validation fails:
- ❌ Fix issues before proceeding
- ❌ Don't waste time on broken pipeline

### **Step 3: Post-Processing Quality Check**
```bash
# After each stage, check quality
python scripts/data_quality_dashboard.py --client "NewClient"
```

## 🛠️ **Common Issues & Solutions**

### **Issue: CSV Column Mismatches**
**Symptoms:** "Missing required columns" error
**Solution:** Use CSV validator - it auto-fixes 90% of column issues

### **Issue: Too Many Themes Generated**
**Symptoms:** 100+ themes overwhelming the workbook
**Solution:** Use theme limiter to enforce 5 themes per interview max

### **Issue: Database Constraint Violations**
**Symptoms:** "origin_check" constraint errors
**Solution:** Use database validator to identify and fix constraint issues

### **Issue: Poor Data Quality**
**Symptoms:** Missing company names, empty transcripts
**Solution:** Use data quality dashboard to identify and fix data issues

## 📊 **Validation Report Example**

```
================================================================================
VOC PIPELINE VALIDATION SUMMARY
================================================================================
Client: NewClient
Timestamp: 2025-01-27 15:30:00

📋 CSV Validation: ✅ PASSED
   📁 Validated file: interviews_VALIDATED.csv

🗄️ Database Validation: ✅ PASSED

🎯 Theme Limits Check: ✅ PASSED

🔍 Data Quality Check: ✅ PASSED

📊 OVERALL VALIDATION STATUS:
🎉 ALL CRITICAL VALIDATIONS PASSED
   Pipeline is ready for processing
   Use validated CSV: interviews_VALIDATED.csv
================================================================================
```

## 🎯 **What This Prevents**

### **Before (ShipBob Experience):**
- ❌ 2+ hours debugging CSV column issues
- ❌ Database constraint errors mid-process
- ❌ 103 themes overwhelming the workbook
- ❌ Poor data quality causing failures
- ❌ Manual fixes at every stage

### **After (With Validation System):**
- ✅ 15 minutes of automated validation
- ✅ All issues caught and auto-fixed upfront
- ✅ Guaranteed 5 themes per interview max
- ✅ High-quality data from the start
- ✅ Smooth processing with checkpoints

## 🚨 **Critical Success Factors**

1. **Always run validation before processing** - Don't skip this step
2. **Use the validated CSV** - Don't use the original if validation made fixes
3. **Check quality after each stage** - Catch issues early
4. **Fix issues before proceeding** - Don't try to work around problems

## 💡 **Pro Tips**

- Run validation in the morning before starting work
- Save validation reports for audit trails
- Use the `--output` flag to save reports
- Check data quality dashboard after each major stage
- If validation fails, fix the root cause, not the symptom

## 🔧 **Troubleshooting**

### **Validation Script Won't Run:**
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Activate virtual environment
source venv/bin/activate
```

### **Database Connection Fails:**
- Check environment variables
- Verify Supabase credentials
- Check network connectivity

### **CSV Validation Fails:**
- Check file encoding (try UTF-8)
- Verify file isn't corrupted
- Check file permissions

---

**Remember:** 15 minutes of validation saves 2+ hours of debugging. Always validate first! 