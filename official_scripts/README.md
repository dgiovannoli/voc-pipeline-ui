# Official Scripts

This directory contains the production-ready scripts for the VOC Pipeline UI, organized by functionality.

## Directory Structure

```
official_scripts/
├── core_analytics/           # Analysis and processing scripts
├── ui_components/           # Streamlit UI applications
├── database/                # Database interaction modules
├── utilities/               # Helper functions and utilities
├── rev_theme_story_scorecard.py  # Theme-driven story reports
└── README.md                # This documentation
```

## Core Analytics Scripts

### `core_analytics/enhanced_stage2_analyzer.py`
**Purpose**: Enhanced Stage 2 analysis with improved scoring and evidence integration
**Key Features**:
- Advanced sentiment analysis
- Evidence strength scoring
- Competitive intelligence insights
- Statistical confidence intervals

### `core_analytics/stage3_findings_analyzer.py`
**Purpose**: Stage 3 findings analysis and processing
**Key Features**:
- Findings extraction and analysis
- Quote validation and processing
- Evidence matrix generation

### `core_analytics/stage3_findings_analyzer_enhanced.py`
**Purpose**: Enhanced Stage 3 analysis with advanced features
**Key Features**:
- Improved findings processing
- Enhanced evidence linking
- Advanced analytics capabilities

### `core_analytics/stage4_theme_generator.py`
**Purpose**: Stage 4 theme generation and analysis
**Key Features**:
- Theme extraction and classification
- Win/loss categorization
- Strategic insights generation

### `core_analytics/competitive_intelligence_analyzer.py`
**Purpose**: Competitive intelligence analysis
**Key Features**:
- Competitive landscape analysis
- Market positioning insights
- Strategic recommendations

### `core_analytics/enhanced_competitive_intelligence.py`
**Purpose**: Enhanced competitive intelligence with advanced analytics
**Key Features**:
- Advanced competitive analysis
- Market trend identification
- Strategic positioning insights

### `core_analytics/client_specific_classifier.py`
**Purpose**: Client-specific classification and analysis
**Key Features**:
- Client-specific insights
- Custom classification logic
- Tailored analysis capabilities

## UI Components

### `ui_components/app.py`
**Purpose**: Main Streamlit application
**Usage**: `streamlit run official_scripts/ui_components/app.py`

### `ui_components/stage1_ui.py`
**Purpose**: Stage 1 UI interface
**Usage**: `streamlit run official_scripts/ui_components/stage1_ui.py`

### `ui_components/stage2_ui.py`
**Purpose**: Stage 2 UI interface
**Usage**: `streamlit run official_scripts/ui_components/stage2_ui.py`

### `ui_components/stage3_ui.py`
**Purpose**: Stage 3 UI interface
**Usage**: `streamlit run official_scripts/ui_components/stage3_ui.py`

### `ui_components/stage4_ui.py`
**Purpose**: Stage 4 UI interface
**Usage**: `streamlit run official_scripts/ui_components/stage4_ui.py`

### `ui_components/admin_ui.py`
**Purpose**: Admin interface
**Usage**: `streamlit run official_scripts/ui_components/admin_ui.py`

### `ui_components/curation_ui.py`
**Purpose**: Curation interface
**Usage**: `streamlit run official_scripts/ui_components/curation_ui.py`

### `ui_components/competitive_intelligence_ui.py`
**Purpose**: Competitive intelligence UI
**Usage**: `streamlit run official_scripts/ui_components/competitive_intelligence_ui.py`

### `ui_components/production_dashboard.py`
**Purpose**: Production dashboard
**Usage**: `streamlit run official_scripts/ui_components/production_dashboard.py`

## Database

### `database/supabase_database.py`
**Purpose**: Supabase database interface
**Key Features**:
- Database connection management
- Data retrieval and storage
- Query optimization

## Utilities

### `utilities/metadata_stage1_processor.py`
**Purpose**: Stage 1 metadata processing
**Key Features**:
- Metadata extraction
- Data validation
- Processing utilities

### `utilities/embedding_utils.py`
**Purpose**: Embedding utilities
**Key Features**:
- Text embedding generation
- Similarity calculations
- Vector operations

## Report Generation

### `rev_theme_story_scorecard.py`
**Purpose**: Generate theme-driven story reports anchored by scorecard framework
**Key Features**:
- Themes tell the story, findings/quotes provide evidence
- Scorecard framework anchors the Win/Loss report
- Comprehensive evidence matrix linking themes to data
- Executive summary with strategic implications

**Usage**:
```bash
python official_scripts/rev_theme_story_scorecard.py
```

**Output**: `reports/REV_THEME_STORY_REPORT.txt`

## Script Development History

All draft versions and experimental scripts are stored in `../drafts/report_generation/` for reference.

## Version Control

- **Official scripts**: Committed to git
- **Draft scripts**: Excluded via .gitignore
- **Report outputs**: Excluded via .gitignore (generated on-demand)

## Maintenance

When updating official scripts:
1. Test thoroughly
2. Update this README
3. Move old version to drafts/ if needed
4. Commit changes

## Import Structure

Scripts use relative imports to maintain functionality:

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from official_scripts.database.supabase_database import SupabaseDatabase
``` 