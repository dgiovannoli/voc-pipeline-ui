# Streamlit UI Integration with Stage 2 Database Analyzer

## Overview

The Streamlit UI now includes full integration with the new Stage 2 database analyzer, providing a seamless workflow from Stage 1 extraction to Stage 2 analysis and trend visualization.

## New Workflow Steps

### 1. 📁 Upload & Process (Stage 1)
- Upload interview transcripts
- Extract core responses using modular processor
- Save results to CSV and database

### 2. 📊 Stage 1 Results
- View extracted quotes and responses
- Validate data quality
- Export Stage 1 results

### 3. 🎯 Stage 2 Analysis (NEW)
- Save Stage 1 data to database
- Run Stage 2 quote analysis against 10-criteria framework
- View analysis results and metrics
- Force reprocess if needed

### 4. 📈 Trends & Insights (NEW)
- Visualize performance trends over time
- Filter by company and time period
- Identify improving/declining criteria
- Track competitive performance

### 5. 💾 Export Data
- Export Stage 1 and Stage 2 results
- Generate reports and insights

## Key Features Added

### Database Integration
- **Automatic Database Creation**: SQLite database created on first run
- **Stage 1 to Database**: One-click save of Stage 1 results to database
- **Incremental Processing**: Only analyze new quotes by default
- **Data Persistence**: All analysis results stored in database

### Stage 2 Analysis UI
- **Run Analysis**: Execute Stage 2 analysis with progress tracking
- **Force Reprocess**: Re-analyze all quotes (useful after config changes)
- **Real-time Metrics**: Processing time, success rate, coverage
- **Criteria Performance**: Top performing criteria with scores
- **Raw Data View**: Detailed analysis results in table format

### Trend Visualization
- **Interactive Charts**: Plotly-based trend charts
- **Company Filtering**: Filter trends by specific companies
- **Time Period Selection**: Analyze trends over 3-12 months
- **Improvement Tracking**: Identify improving and declining criteria
- **Performance Metrics**: Average scores and quote counts

## Database Schema

The integration uses three main tables:

### `core_responses` (Stage 1 Output)
- Stores extracted quotes and metadata
- Source of truth for all analysis

### `quote_analysis` (Stage 2 Output)
- Stores scores for each quote against 10 criteria
- Includes deal weighting and context assessment
- Links back to original quotes via foreign key

### `trend_analysis` (Trend Data)
- Monthly performance metrics by company and criterion
- Enables trend visualization and reporting

## Usage Workflow

### Step 1: Upload and Process
1. Upload interview transcripts
2. Run Stage 1 extraction
3. Review extracted quotes

### Step 2: Stage 2 Analysis
1. Click "💾 Save Stage 1 to Database"
2. Click "🚀 Run Stage 2 Analysis"
3. Review analysis results and metrics

### Step 3: Trends and Insights
1. Navigate to "📈 Trends & Insights"
2. Select company and time period
3. Analyze performance trends
4. Identify areas for improvement

## Configuration

The Stage 2 analysis uses the same configuration file (`config/analysis_config.yaml`) as the standalone analyzer:

- **Scoring weights** and deal outcome multipliers
- **Processing parameters** (workers, batch size, etc.)
- **Criteria definitions** and keywords
- **Quality thresholds** and confidence levels

## Benefits

### Seamless Integration
- **Single UI**: Everything in one Streamlit app
- **Consistent Workflow**: Clear step-by-step process
- **Data Continuity**: Stage 1 → Database → Stage 2 → Trends

### Real-time Insights
- **Live Metrics**: Processing time and success rates
- **Interactive Charts**: Explore trends dynamically
- **Immediate Feedback**: See results as they're processed

### Business Intelligence
- **Executive Dashboards**: High-level performance metrics
- **Trend Analysis**: Track improvements over time
- **Competitive Insights**: Compare performance across companies

## Technical Implementation

### Database Functions
- `init_database()`: Creates database schema
- `save_stage1_to_database()`: Migrates CSV to database
- `run_stage2_analysis()`: Executes Stage 2 analysis
- `get_stage2_summary()`: Retrieves analysis statistics
- `get_trend_data()`: Gets trend data for visualization

### UI Components
- `show_stage2_analysis()`: Stage 2 analysis interface
- `show_trends_insights()`: Trend visualization interface
- `create_trend_chart()`: Generates Plotly charts

### Error Handling
- Database connection errors
- Analysis failures
- Missing data scenarios
- Configuration issues

## Next Steps

1. **Install Dependencies**: `pip install plotly pyyaml`
2. **Run Streamlit**: `streamlit run app.py`
3. **Test Workflow**: Upload → Stage 1 → Stage 2 → Trends
4. **Customize Config**: Adjust analysis parameters as needed

## Troubleshooting

### Common Issues
- **Missing Dependencies**: Install plotly and pyyaml
- **Database Errors**: Check file permissions and disk space
- **Analysis Failures**: Verify OpenAI API key and quota
- **Trend Data Missing**: Run Stage 2 analysis first

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export STREAMLIT_LOG_LEVEL=debug
streamlit run app.py
``` 