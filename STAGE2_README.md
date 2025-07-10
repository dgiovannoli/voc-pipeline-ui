# Stage 2: Database-First Quote Analysis

## Overview

The new Stage 2 analyzer addresses all the major issues with the previous CSV-based approach:

✅ **No Redundant Processing** - Works with existing Stage 1 quotes  
✅ **Database Integration** - Uses SQLite instead of CSV files  
✅ **Memory Efficient** - Processes quotes in batches  
✅ **Incremental Processing** - Only analyzes new quotes by default  
✅ **Smart Deal Weighting** - Context-aware scoring, not just positive/negative  
✅ **Trend Analysis** - Tracks performance over time with dates  
✅ **Relative Scoring** - Scores are calibrated against your data  

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_stage2.txt
```

### 2. Migrate Existing Data
```bash
# Migrate your Stage 1 CSV to the database
python migrate_to_database.py your_stage1_output.csv
```

### 3. Run Stage 2 Analysis
```bash
# Analyze only new quotes (incremental)
python run_stage2.py

# Force reprocess all quotes
python run_stage2.py --force

# Show trends after analysis
python run_stage2.py --trends

# Filter trends by company
python run_stage2.py --trends --company "Luminos Law"
```

## Key Improvements

### 🗄️ Database-First Architecture
- **Source of Truth**: `stage1_data_responses` table stores Stage 1 output
- **Analysis Layer**: `stage2_response_labeling` table stores Stage 2 scores
- **Trend Tracking**: `trend_analysis` table tracks performance over time
- **Metadata**: `processing_metadata` table tracks processing history

### 🧠 Smart Deal Weighting
Instead of simple positive/negative weighting:
```python
# OLD: Simple positive/negative
if deal_status == "lost" and score < 0:
    return score * 1.3  # Always amplify negative feedback

# NEW: Context-aware weighting
if context == "deal_breaking":
    return score * 1.5  # Amplify truly critical feedback
elif context == "minor":
    return score * 0.7  # Reduce minor feedback impact
```

### 📈 Trend Analysis
- Tracks performance by company, criterion, and month
- Identifies improving/declining areas over time
- Supports executive reporting and KPI tracking

### ⚙️ Configuration Management
All settings in `config/analysis_config.yaml`:
- Scoring scales and weights
- Processing parameters
- Criteria definitions
- Quality thresholds

## Database Schema

### Core Responses (Stage 1 Output)
```sql
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Quote Analysis (Stage 2 Output)
```sql
CREATE TABLE stage2_response_labeling (
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id VARCHAR,
    criterion VARCHAR NOT NULL,
    score DECIMAL(3,2),
    priority VARCHAR CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    confidence VARCHAR CHECK (confidence IN ('high', 'medium', 'low')),
    relevance_explanation TEXT,
    deal_weighted_score DECIMAL(3,2),
    context_keywords TEXT,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES stage1_data_responses(response_id),
    UNIQUE(quote_id, criterion)
);
```

### Trend Analysis
```sql
CREATE TABLE trend_analysis (
    trend_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company VARCHAR,
    criterion VARCHAR,
    month_year VARCHAR(7),  -- YYYY-MM format
    avg_score DECIMAL(3,2),
    quote_count INTEGER,
    deal_outcome_distribution TEXT,  -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company, criterion, month_year)
);
```

## Usage Examples

### Basic Analysis
```python
from enhanced_stage2_analyzer import DatabaseStage2Analyzer

analyzer = DatabaseStage2Analyzer()
result = analyzer.process_incremental()
print(f"Processed {result['quotes_analyzed']} quotes")
```

### Get Trend Data
```python
# Get trends for last 6 months
trends = analyzer.get_trend_data(months=6)

# Get trends for specific company
company_trends = analyzer.get_trend_data(
    company="Luminos Law", 
    months=12
)
```

### Force Reprocess
```python
# Reprocess all quotes (e.g., after config changes)
result = analyzer.process_incremental(force_reprocess=True)
```

## Configuration

Edit `config/analysis_config.yaml` to customize:

### Scoring Weights
```yaml
scoring:
  deal_weighting:
    lost_deal_base: 1.2      # Lost deals get more attention
    won_deal_base: 0.9       # Won deals get less attention
    critical_multiplier: 1.5  # Amplify truly critical feedback
    minor_multiplier: 0.7     # Reduce minor feedback impact
```

### Processing Settings
```yaml
processing:
  max_workers: 4             # Parallel processing
  max_quote_length: 1000     # LLM input limit
  retry_attempts: 3          # Error recovery
  batch_size: 50             # Memory efficiency
```

### Criteria Definitions
```yaml
criteria:
  product_capability:
    description: "Functionality, features, performance, and core solution fit"
    weight: 1.0
    priority_threshold: 0.8
    keywords: ["accuracy", "features", "performance"]
```

## Benefits

### 🚀 Performance
- **Incremental Processing**: Only analyze new quotes
- **Parallel Processing**: Configurable worker threads
- **Memory Efficient**: Batch processing, not load-all-in-memory
- **Error Recovery**: Automatic retries with exponential backoff

### 📊 Intelligence
- **Context-Aware Scoring**: Understands deal-breaking vs minor feedback
- **Relative Scoring**: Calibrated against your data, not arbitrary
- **Trend Tracking**: Performance monitoring over time
- **Quality Metrics**: Confidence levels and error tracking

### 🔧 Maintainability
- **Configuration-Driven**: No code changes for adjustments
- **Database Integrity**: Foreign keys and constraints
- **Logging**: Comprehensive error tracking and debugging
- **Modular Design**: Easy to extend and modify

## Migration from Old System

1. **Backup your data**: Copy existing CSV files
2. **Migrate to database**: Use `migrate_to_database.py`
3. **Run new analysis**: Use `run_stage2.py`
4. **Compare results**: Check database vs old JSON outputs
5. **Update workflows**: Point to new database instead of CSV files

## Next Steps

- [ ] Integrate with Streamlit UI
- [ ] Add competitive benchmarking
- [ ] Implement executive dashboards
- [ ] Add automated trend alerts
- [ ] Create API endpoints for external tools 