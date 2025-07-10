# Stage 3: Findings Identification

## Overview

Stage 3 is the final phase of the VOC Pipeline that transforms scored quotes from Stage 2 into executive-ready findings. It identifies recurring patterns across companies, calculates confidence scores, and generates actionable insights for business decision-making.

## What Stage 3 Does

### 🎯 **Pattern Recognition**
- Analyzes scored quotes across multiple companies
- Identifies recurring themes and patterns
- Groups similar feedback by criterion and company

### 📊 **Confidence Scoring**
- Calculates confidence scores using multipliers:
  - High confidence: 1.5x multiplier
  - Medium confidence: 1.0x multiplier  
  - Low confidence: 0.7x multiplier
- Applies weighted scoring based on quote strength and confidence

### 🔍 **Finding Generation**
- Creates four types of findings:
  - **Strength**: High-performing areas (scores ≥ 3.5)
  - **Improvement**: Areas needing attention (scores ≤ 2.0)
  - **Positive Trend**: Consistent positive feedback across companies
  - **Negative Trend**: Consistent negative feedback across companies

### 📈 **Executive Insights**
- Generates business-ready findings with:
  - Impact scores (0-5 scale)
  - Confidence levels
  - Sample supporting quotes
  - Key themes identified
  - Company coverage statistics

## Architecture

### Database Schema

The `findings` table stores all generated findings:

```sql
CREATE TABLE findings (
    id SERIAL PRIMARY KEY,
    criterion VARCHAR(100) NOT NULL,
    finding_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    impact_score DECIMAL(3,2) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    companies_affected INTEGER NOT NULL,
    quote_count INTEGER NOT NULL,
    sample_quotes JSONB,
    themes JSONB,
    generated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Key Components

1. **Stage3FindingsAnalyzer**: Main analysis engine
2. **SupabaseDatabase**: Database operations for findings
3. **Streamlit UI**: Interactive findings display and generation

## Configuration

### Pattern Thresholds
```yaml
stage3:
  pattern_thresholds:
    minimum_quotes: 3          # Minimum quotes to form a pattern
    minimum_companies: 2       # Minimum companies for cross-company pattern
    confidence_threshold: 0.6  # Minimum confidence for valid pattern
  confidence_multipliers:
    high_confidence: 1.5
    medium_confidence: 1.0
    low_confidence: 0.7
```

### Finding Types
- **strength**: Areas of excellence (high scores)
- **improvement**: Areas needing attention (low scores)
- **positive_trend**: Consistent positive feedback
- **negative_trend**: Consistent negative feedback

## Usage

### Command Line
```bash
# Run Stage 3 analysis
python run_stage3.py

# Or use the module directly
python -c "from stage3_findings_analyzer import Stage3FindingsAnalyzer; Stage3FindingsAnalyzer().process_findings()"
```

### Streamlit UI
1. Navigate to "🎯 Stage 3 Findings" in the sidebar
2. Click "🎯 Generate New Findings" to run analysis
3. View and filter findings by criterion and type
4. Export findings as CSV

### Programmatic Usage
```python
from stage3_findings_analyzer import Stage3FindingsAnalyzer

# Initialize analyzer
analyzer = Stage3FindingsAnalyzer()

# Run analysis
result = analyzer.process_findings()

# Access findings
findings_df = analyzer.db.get_findings()
summary = analyzer.db.get_findings_summary()
```

## Output Format

### Finding Structure
Each finding contains:
- **Title**: Concise finding title
- **Description**: Detailed explanation with business context
- **Impact Score**: 0-5 scale indicating business impact
- **Confidence Score**: 0-1 scale indicating reliability
- **Companies Affected**: Number of companies this applies to
- **Sample Quotes**: Supporting evidence from interviews
- **Themes**: Key themes identified in the feedback

### Example Finding
```json
{
  "criterion": "product_capability",
  "finding_type": "strength",
  "title": "Product Capability Strength",
  "description": "Customers consistently praise the product's ease of use and accuracy, with 3 companies reporting significant time savings.",
  "impact_score": 4.2,
  "confidence_score": 0.85,
  "companies_affected": 3,
  "quote_count": 8,
  "sample_quotes": ["The product is incredibly easy to use", "Accuracy is excellent"],
  "themes": ["ease_of_use", "accuracy"]
}
```

## Integration with Pipeline

### Prerequisites
- Stage 1: Core response extraction completed
- Stage 2: Quote scoring and analysis completed
- Supabase database with `stage1_data_responses` and `stage2_response_labeling` tables

### Data Flow
1. **Input**: Scored quotes from Stage 2 (`stage2_response_labeling` table)
2. **Processing**: Pattern recognition and confidence scoring
3. **Output**: Executive findings stored in `findings` table
4. **Display**: Interactive UI for viewing and filtering findings

## Performance Considerations

### Batch Processing
- Processes quotes in configurable batches (default: 100)
- Uses parallel processing for pattern analysis
- Optimized database queries with proper indexing

### Memory Management
- Streams data from database to avoid memory issues
- Processes patterns incrementally
- Cleans up temporary data structures

## Troubleshooting

### Common Issues

**No findings generated**
- Check that Stage 2 analysis has been completed
- Verify that scored quotes exist in the database
- Ensure pattern thresholds are not too restrictive

**Low confidence scores**
- Review confidence multipliers in configuration
- Check that quotes have proper confidence levels from Stage 2
- Consider adjusting confidence thresholds

**Missing themes**
- Verify that relevance explanations are being captured in Stage 2
- Check theme extraction logic in `_extract_themes` method

### Debug Mode
Enable debug logging to see detailed processing information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
- **Advanced Pattern Recognition**: Machine learning-based pattern detection
- **Trend Analysis**: Time-based trend identification
- **Competitive Analysis**: Comparison with competitor feedback
- **Actionable Recommendations**: AI-generated action items
- **Executive Dashboards**: High-level summary views

### Customization Options
- **Custom Finding Types**: User-defined finding categories
- **Industry-Specific Themes**: Tailored theme extraction
- **Custom Confidence Models**: Advanced confidence calculation
- **Integration APIs**: Export to business intelligence tools

## Support

For issues or questions about Stage 3:
1. Check the troubleshooting section above
2. Review the configuration settings
3. Verify database connectivity and schema
4. Check the logs for detailed error messages

---

**Stage 3 transforms raw customer feedback into actionable business intelligence, providing executives with the insights they need to make informed decisions.** 