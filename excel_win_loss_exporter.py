#!/usr/bin/env python3
"""
Excel Win-Loss Report Exporter
Creates analyst-ready multi-tab Excel workbooks for theme curation workflow.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import xlsxwriter
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExcelWinLossExporter:
    """
    Create comprehensive Excel workbooks for analyst curation workflow.
    
    Features:
    - Multiple tabs for different analysis phases
    - Pre-formatted cells for Include/Exclude decisions
    - Conditional formatting for priority themes
    - Summary dashboards for quick overview
    """
    
    def __init__(self):
        self.workbook = None
        self.formats = {}
        
    def export_analyst_workbook(self, themes_data: Dict[str, Any], output_path: str = None) -> str:
        """
        Export complete analyst curation workbook.
        
        Args:
            themes_data: Output from WinLossReportGenerator
            output_path: Optional custom output path
            
        Returns:
            Path to generated Excel file
        """
        if not themes_data.get("success"):
            raise ValueError(f"Invalid themes data: {themes_data.get('error')}")
        
        # Generate filename if not provided
        if not output_path:
            client_id = themes_data["metadata"]["client_id"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"Win_Loss_Analyst_Workbook_{client_id}_{timestamp}.xlsx"
        
        logger.info(f"🗂️ Creating analyst workbook: {output_path}")
        
        # Create workbook and define formatting
        self.workbook = xlsxwriter.Workbook(output_path)
        self._define_formats()
        
        try:
            # Tab 1: Executive Summary
            self._create_executive_summary_tab(themes_data)
            
            # Tab 2: Theme Curation Workspace (Main working tab)
            self._create_theme_curation_tab(themes_data)
            
            # Tab 3: Quote Analysis & Selection
            self._create_quote_analysis_tab(themes_data)
            
            # Tab 4: Competitive Intelligence Deep Dive
            self._create_competitive_tab(themes_data)
            
            # Tab 5: Raw Data Reference
            self._create_raw_data_tab(themes_data)
            
            # Tab 6: Report Builder Template
            self._create_report_builder_tab(themes_data)
            
            self.workbook.close()
            
            logger.info(f"✅ Successfully created analyst workbook: {output_path}")
            return output_path
            
        except Exception as e:
            self.workbook.close()
            logger.error(f"❌ Error creating workbook: {e}")
            raise
    
    def _define_formats(self):
        """Define all cell formats used throughout the workbook"""
        self.formats = {
            'title': self.workbook.add_format({
                'bold': True, 'font_size': 16, 'bg_color': '#2F4F4F', 'font_color': 'white',
                'align': 'center', 'valign': 'vcenter'
            }),
            'header': self.workbook.add_format({
                'bold': True, 'font_size': 12, 'bg_color': '#4682B4', 'font_color': 'white',
                'align': 'center', 'valign': 'vcenter', 'text_wrap': True
            }),
            'subheader': self.workbook.add_format({
                'bold': True, 'font_size': 10, 'bg_color': '#B0C4DE', 
                'align': 'left', 'valign': 'vcenter'
            }),
            'strength': self.workbook.add_format({
                'bg_color': '#90EE90', 'font_color': '#006400', 'bold': True
            }),
            'weakness': self.workbook.add_format({
                'bg_color': '#FFB6C1', 'font_color': '#8B0000', 'bold': True
            }),
            'mixed_signal': self.workbook.add_format({
                'bg_color': '#FFD700', 'font_color': '#FF8C00', 'bold': True
            }),
            'high_priority': self.workbook.add_format({
                'bg_color': '#FF6347', 'font_color': 'white', 'bold': True
            }),
            'decision_cell': self.workbook.add_format({
                'bg_color': '#F0F8FF', 'align': 'center', 'border': 1
            }),
            'notes_cell': self.workbook.add_format({
                'bg_color': '#FFFACD', 'text_wrap': True, 'valign': 'top'
            }),
            'data_cell': self.workbook.add_format({
                'text_wrap': True, 'valign': 'top', 'border': 1
            }),
            'number': self.workbook.add_format({
                'num_format': '0.0', 'align': 'center'
            }),
            'percentage': self.workbook.add_format({
                'num_format': '0%', 'align': 'center'
            })
        }
    
    def _create_executive_summary_tab(self, themes_data: Dict[str, Any]):
        """Create executive summary dashboard tab"""
        worksheet = self.workbook.add_worksheet('📊 Executive Summary')
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:F', 15)
        
        # Title
        worksheet.merge_range('A1:F1', f"Win-Loss Analysis Executive Summary - {themes_data['metadata']['client_id']}", self.formats['title'])
        
        # Metadata section
        row = 3
        worksheet.write(row, 0, "Analysis Overview", self.formats['subheader'])
        row += 1
        worksheet.write(row, 0, "Generated On:")
        worksheet.write(row, 1, themes_data['metadata']['generated_at'][:10])
        row += 1
        worksheet.write(row, 0, "Total Quotes Analyzed:")
        worksheet.write(row, 1, themes_data['metadata']['total_quotes'])
        row += 1
        worksheet.write(row, 0, "Companies Analyzed:")
        worksheet.write(row, 1, themes_data['metadata']['companies_analyzed'])
        row += 1
        worksheet.write(row, 0, "High-Quality Themes Generated:")
        worksheet.write(row, 1, themes_data['metadata']['total_themes'])
        
        # Themes summary
        row += 3
        worksheet.write(row, 0, "Theme Summary by Type", self.formats['subheader'])
        row += 1
        
        # Headers
        headers = ["Theme Type", "Count", "Avg Quality Score", "Total Quotes", "Key Insights"]
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1
        
        # Theme type summaries
        theme_summaries = self._summarize_themes_by_type(themes_data['themes'])
        for theme_type, summary in theme_summaries.items():
            theme_format = self.formats.get(theme_type, self.formats['data_cell'])
            worksheet.write(row, 0, theme_type.replace('_', ' ').title(), theme_format)
            worksheet.write(row, 1, summary['count'])
            worksheet.write(row, 2, summary['avg_quality_score'], self.formats['number'])
            worksheet.write(row, 3, summary['total_quotes'])
            worksheet.write(row, 4, summary['key_insight'], self.formats['data_cell'])
            row += 1
        
        # Key recommendations section
        row += 2
        worksheet.write(row, 0, "Analyst Action Items", self.formats['subheader'])
        row += 1
        
        recommendations = [
            "1. Review Theme Curation tab - approve/reject themes for final report",
            "2. Analyze Quote Selection tab - choose best supporting evidence", 
            "3. Examine Competitive Intelligence for market positioning insights",
            "4. Use Report Builder tab to draft executive presentation",
            "5. Cross-reference Raw Data for additional context when needed"
        ]
        
        for rec in recommendations:
            worksheet.write(row, 0, rec, self.formats['data_cell'])
            row += 1
    
    def _create_theme_curation_tab(self, themes_data: Dict[str, Any]):
        """Create the main theme curation workspace"""
        worksheet = self.workbook.add_worksheet('🎯 Theme Curation')
        
        # Set column widths
        worksheet.set_column('A:A', 12)  # Theme ID
        worksheet.set_column('B:B', 60)  # Theme Statement  
        worksheet.set_column('C:C', 15)  # Theme Type
        worksheet.set_column('D:D', 20)  # Subject
        worksheet.set_column('E:E', 12)  # Quality Score
        worksheet.set_column('F:F', 20)  # Company Distribution
        worksheet.set_column('G:G', 50)  # Evidence Preview
        worksheet.set_column('H:H', 15)  # Quality Flags
        worksheet.set_column('I:I', 15)  # Analyst Decision
        worksheet.set_column('J:J', 40)  # Analyst Notes
        worksheet.set_column('K:K', 15)  # Priority Level
        
        # Title
        worksheet.merge_range('A1:K1', "Theme Curation Workspace - Make Include/Exclude Decisions", self.formats['title'])
        
        # Instructions
        worksheet.merge_range('A2:K2', "INSTRUCTIONS: Review evidence preview in Column G before making Include/Exclude decisions in Column I. Quality flags in Column H indicate confidence level.", self.formats['subheader'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Type", "Subject Category", 
            "Quality Score", "Company Distribution", "Evidence Preview", "Quality Flags",
            "Decision (INCLUDE/EXCLUDE)", "Analyst Notes", "Priority Level"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Theme data
        row = 4
        for theme in themes_data['themes']:
            # Theme ID
            worksheet.write(row, 0, theme['theme_id'])
            
            # Theme Statement
            worksheet.write(row, 1, theme['theme_statement'], self.formats['data_cell'])
            
            # Theme Type with formatting
            theme_type = theme['theme_type']
            theme_format = self.formats.get(theme_type, self.formats['data_cell'])
            worksheet.write(row, 2, theme_type.replace('_', ' ').title(), theme_format)
            
            # Subject Category
            worksheet.write(row, 3, theme['harmonized_subject'])
            
            # Quality Score
            worksheet.write(row, 4, theme['validation_metrics']['quality_score'], self.formats['number'])
            
            # Company Distribution
            company_dist = theme['validation_metrics'].get('company_distribution', {})
            dist_summary = company_dist.get('distribution_summary', f"{theme['validation_metrics']['companies_count']} companies")
            worksheet.write(row, 5, dist_summary, self.formats['data_cell'])
            
            # Evidence Preview (Top 2 supporting quotes)
            evidence_preview = self._create_evidence_preview(theme)
            worksheet.write(row, 6, evidence_preview, self.formats['data_cell'])
            
            # Quality Flags
            quality_flags = self._assign_quality_flags(theme)
            worksheet.write(row, 7, ", ".join(quality_flags), self.formats['data_cell'])
            
            # Decision Cell (dropdown)
            worksheet.data_validation(row, 8, row, 8, {
                'validate': 'list',
                'source': ['INCLUDE', 'EXCLUDE', 'REVIEW']
            })
            worksheet.write(row, 8, "", self.formats['decision_cell'])
            
            # Notes Cell
            worksheet.write(row, 9, "", self.formats['notes_cell'])
            
            # Priority Cell (dropdown)
            worksheet.data_validation(row, 10, row, 10, {
                'validate': 'list', 
                'source': ['HIGH', 'MEDIUM', 'LOW']
            })
            worksheet.write(row, 10, "", self.formats['decision_cell'])
            
            row += 1
        
        # Add conditional formatting for theme types
        worksheet.conditional_format(f'C4:C{row}', {
            'type': 'text',
            'criteria': 'containing',
            'value': 'Strength',
            'format': self.formats['strength']
        })
        
        worksheet.conditional_format(f'C4:C{row}', {
            'type': 'text', 
            'criteria': 'containing',
            'value': 'Weakness',
            'format': self.formats['weakness']
        })
    
    def _create_quote_analysis_tab(self, themes_data: Dict[str, Any]):
        """Create detailed quote analysis and selection tab"""
        worksheet = self.workbook.add_worksheet('💬 Quote Analysis')
        
        # Set column widths
        worksheet.set_column('A:A', 12)  # Response ID
        worksheet.set_column('B:B', 40)  # Original Question
        worksheet.set_column('C:C', 12)  # Theme ID
        worksheet.set_column('D:D', 50)  # Full Theme Statement
        worksheet.set_column('E:E', 50)  # Verbatim Quote
        worksheet.set_column('F:F', 12)  # Sentiment
        worksheet.set_column('G:G', 12)  # Impact Score
        worksheet.set_column('H:H', 15)  # Company
        worksheet.set_column('I:I', 15)  # Interviewee
        worksheet.set_column('J:J', 15)  # Use in Report?
        worksheet.set_column('K:K', 30)  # Quote Notes
        
        # Title
        worksheet.merge_range('A1:K1', "Quote Analysis & Selection for Final Report", self.formats['title'])
        
        # Headers
        headers = [
            "Response ID", "Original Question", "Theme ID", "Full Theme Statement",
            "Verbatim Quote", "Sentiment", "Impact Score", "Company", "Interviewee", 
            "Use in Report?", "Quote Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.formats['header'])
        
        # Quote data
        row = 3
        for theme in themes_data['themes']:
            for quote in theme['all_quotes']:
                # Response ID
                worksheet.write(row, 0, quote.get('response_id', ''))
                
                # Original Question
                worksheet.write(row, 1, quote.get('question', 'Question not available'), self.formats['data_cell'])
                
                # Theme ID
                worksheet.write(row, 2, theme['theme_id'])
                
                # Full Theme Statement
                worksheet.write(row, 3, theme['theme_statement'], self.formats['data_cell'])
                
                # Verbatim Quote
                worksheet.write(row, 4, quote['verbatim_response'], self.formats['data_cell'])
                
                # Sentiment
                sentiment = quote.get('sentiment', 'unknown').title()
                worksheet.write(row, 5, sentiment)
                
                # Impact Score
                worksheet.write(row, 6, quote.get('impact_score', 0), self.formats['number'])
                
                # Company (handle both column names)
                company = quote.get('company', quote.get('company_name', 'Unknown'))
                worksheet.write(row, 7, company)
                
                # Interviewee
                worksheet.write(row, 8, quote.get('interviewee_name', ''))
                
                # Use in Report dropdown
                worksheet.data_validation(row, 9, row, 9, {
                    'validate': 'list',
                    'source': ['YES', 'NO', 'MAYBE']
                })
                worksheet.write(row, 9, "", self.formats['decision_cell'])
                
                # Quote Notes
                worksheet.write(row, 10, "", self.formats['notes_cell'])
                
                row += 1
    
    def _create_competitive_tab(self, themes_data: Dict[str, Any]):
        """Create competitive intelligence deep dive tab"""
        worksheet = self.workbook.add_worksheet('🏆 Competitive Intel')
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Theme Type
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 40)  # Verbatim Quote
        worksheet.set_column('D:D', 20)  # Competitive Insight
        worksheet.set_column('E:E', 15)  # Company
        worksheet.set_column('F:F', 12)  # Impact Score
        worksheet.set_column('G:G', 30)  # Strategic Implication
        
        # Title
        worksheet.merge_range('A1:G1', "Competitive Intelligence & Market Positioning Analysis", self.formats['title'])
        
        # Headers
        headers = [
            "Theme Type", "Theme Statement", "Key Quote", "Competitive Insight", 
            "Company", "Impact Score", "Strategic Implication"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.formats['header'])
        
        # Competitive data - focus on themes flagged as competitive
        row = 3
        for theme in themes_data['themes']:
            if theme.get('competitive_flag', False):
                # Show top quotes for competitive themes
                for quote in theme['supporting_quotes'][:3]:  # Top 3 quotes
                    worksheet.write(row, 0, theme['theme_type'].replace('_', ' ').title())
                    worksheet.write(row, 1, theme['theme_statement'], self.formats['data_cell'])
                    worksheet.write(row, 2, quote['quote_text'], self.formats['data_cell'])
                    worksheet.write(row, 3, self._extract_competitive_insight(quote['quote_text']), self.formats['data_cell'])
                    worksheet.write(row, 4, quote['company'])
                    worksheet.write(row, 5, quote['impact_score'], self.formats['number'])
                    worksheet.write(row, 6, "", self.formats['notes_cell'])  # For analyst to fill
                    row += 1
    
    def _create_raw_data_tab(self, themes_data: Dict[str, Any]):
        """Create raw data reference tab"""
        worksheet = self.workbook.add_worksheet('📋 Raw Data')
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Response ID
        worksheet.set_column('B:B', 20)  # Company
        worksheet.set_column('C:C', 15)  # Interviewee
        worksheet.set_column('D:D', 20)  # Subject
        worksheet.set_column('E:E', 50)  # Question
        worksheet.set_column('F:F', 60)  # Response
        worksheet.set_column('G:G', 12)  # Sentiment
        worksheet.set_column('H:H', 12)  # Impact Score
        
        # Title
        worksheet.merge_range('A1:H1', "Raw Interview Data Reference", self.formats['title'])
        
        # Headers
        headers = [
            "Response ID", "Company", "Interviewee", "Subject", 
            "Original Question", "Verbatim Response", "Sentiment", "Impact Score"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.formats['header'])
        
        # Raw data from all themes
        row = 3
        all_quotes = []
        for theme in themes_data['themes']:
            all_quotes.extend(theme['all_quotes'])
        
        # Remove duplicates by response_id
        seen_ids = set()
        unique_quotes = []
        for quote in all_quotes:
            if quote['response_id'] not in seen_ids:
                unique_quotes.append(quote)
                seen_ids.add(quote['response_id'])
        
        for quote in unique_quotes:
            worksheet.write(row, 0, quote['response_id'])
            company = quote.get('company', quote.get('company_name', 'Unknown'))
            worksheet.write(row, 1, company)
            worksheet.write(row, 2, quote.get('interviewee_name', ''))
            worksheet.write(row, 3, quote.get('subject', ''))
            worksheet.write(row, 4, quote.get('question', ''), self.formats['data_cell'])
            worksheet.write(row, 5, quote['verbatim_response'], self.formats['data_cell'])
            worksheet.write(row, 6, quote.get('sentiment', 'unknown').title())
            worksheet.write(row, 7, quote.get('impact_score', 0), self.formats['number'])
            row += 1
    
    def _create_report_builder_tab(self, themes_data: Dict[str, Any]):
        """Create report builder template tab"""
        worksheet = self.workbook.add_worksheet('📝 Report Builder')
        
        # Set column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 80)
        
        # Title
        worksheet.merge_range('A1:B1', "Executive Report Builder Template", self.formats['title'])
        
        row = 3
        
        # Key Strengths Section
        worksheet.write(row, 0, "🟢 KEY STRENGTHS", self.formats['strength'])
        row += 1
        
        strength_themes = [t for t in themes_data['themes'] if t['theme_type'] == 'strength']
        if strength_themes:
            for theme in strength_themes:
                worksheet.write(row, 0, f"• {theme['theme_id']}")
                worksheet.write(row, 1, theme['theme_statement'], self.formats['data_cell'])
                row += 1
        else:
            worksheet.write(row, 1, "No strength themes identified in current analysis", self.formats['data_cell'])
            row += 1
        
        row += 1
        
        # Key Weaknesses Section  
        worksheet.write(row, 0, "🔴 KEY WEAKNESSES", self.formats['weakness'])
        row += 1
        
        weakness_themes = [t for t in themes_data['themes'] if t['theme_type'] == 'weakness']
        for theme in weakness_themes:
            worksheet.write(row, 0, f"• {theme['theme_id']}")
            worksheet.write(row, 1, theme['theme_statement'], self.formats['data_cell'])
            row += 1
        
        row += 1
        
        # Mixed Signals Section
        worksheet.write(row, 0, "🟡 AREAS FOR INVESTIGATION", self.formats['mixed_signal'])
        row += 1
        
        mixed_themes = [t for t in themes_data['themes'] if t['theme_type'] == 'mixed_signal']
        for theme in mixed_themes:
            worksheet.write(row, 0, f"• {theme['theme_id']}")
            worksheet.write(row, 1, theme['theme_statement'], self.formats['data_cell'])
            row += 1
        
        row += 2
        
        # Action Items Section
        worksheet.write(row, 0, "📋 RECOMMENDED ACTIONS", self.formats['header'])
        row += 1
        
        actions = [
            "1. Address key weaknesses identified in customer feedback",
            "2. Leverage strengths in sales messaging and positioning", 
            "3. Investigate mixed signals for deeper insights",
            "4. Develop competitive response strategies",
            "5. Create follow-up research plan for unclear areas"
        ]
        
        for action in actions:
            worksheet.write(row, 1, action, self.formats['data_cell'])
            row += 1
    
    def _summarize_themes_by_type(self, themes: List[Dict]) -> Dict[str, Dict]:
        """Summarize themes by type for executive overview"""
        summaries = defaultdict(lambda: {
            'count': 0, 
            'total_quotes': 0, 
            'quality_scores': [], 
            'avg_quality_score': 0,
            'key_insight': ''
        })
        
        for theme in themes:
            theme_type = theme['theme_type']
            summaries[theme_type]['count'] += 1
            summaries[theme_type]['total_quotes'] += theme['validation_metrics']['quotes_count']
            summaries[theme_type]['quality_scores'].append(theme['validation_metrics']['quality_score'])
        
        # Calculate averages and insights
        for theme_type, summary in summaries.items():
            if summary['quality_scores']:
                summary['avg_quality_score'] = sum(summary['quality_scores']) / len(summary['quality_scores'])
            
            # Generate key insight
            if theme_type == 'strength':
                summary['key_insight'] = f"Identified {summary['count']} competitive advantages"
            elif theme_type == 'weakness':
                summary['key_insight'] = f"Found {summary['count']} areas requiring immediate attention"
            elif theme_type == 'mixed_signal':
                summary['key_insight'] = f"Discovered {summary['count']} complex patterns needing investigation"
        
        return dict(summaries)
    
    def _extract_competitive_insight(self, quote_text: str) -> str:
        """Extract competitive insight from quote text"""
        text_lower = quote_text.lower()
        
        if 'competitor' in text_lower:
            return "Direct competitive comparison mentioned"
        elif 'alternative' in text_lower:
            return "Alternative solution discussed"  
        elif 'versus' in text_lower or 'vs' in text_lower:
            return "Head-to-head comparison"
        elif 'switch' in text_lower:
            return "Switching consideration mentioned"
        else:
            return "Market positioning insight"
    
    def _create_evidence_preview(self, theme: Dict[str, Any]) -> str:
        """Create evidence preview for theme curation tab"""
        supporting_quotes = theme.get('supporting_quotes', [])
        if not supporting_quotes:
            return "No supporting quotes available"
        
        # Show top 2 quotes with company attribution
        preview_parts = []
        for i, quote in enumerate(supporting_quotes[:2], 1):
            quote_text = quote['quote_text']
            # Truncate long quotes
            if len(quote_text) > 100:
                quote_text = quote_text[:100] + "..."
            
            company = quote.get('company', 'Unknown')
            preview_parts.append(f"{i}. \"{quote_text}\" - {company}")
        
        return "\n\n".join(preview_parts)
    
    def _assign_quality_flags(self, theme: Dict[str, Any]) -> List[str]:
        """Assign quality flags based on theme characteristics"""
        flags = []
        
        metrics = theme.get('validation_metrics', {})
        quality_score = metrics.get('quality_score', 0)
        company_dist = metrics.get('company_distribution', {})
        
        # Quality confidence flags
        if quality_score >= 8.0:
            flags.append("HIGH_CONFIDENCE")
        elif quality_score >= 6.0:
            flags.append("MEDIUM_CONFIDENCE")
        else:
            flags.append("REVIEW_REQUIRED")
        
        # Company distribution flags
        if company_dist.get('total_companies', 0) == 1:
            flags.append("SINGLE_COMPANY")
        elif company_dist.get('bias_warning', False):
            flags.append("COMPANY_BIAS")
        elif company_dist.get('company_balance_score', 0) < 0.3:
            flags.append("UNBALANCED")
        
        # Competitive intelligence flag
        if theme.get('competitive_flag', False):
            flags.append("COMPETITIVE")
        
        return flags

# Test function
def test_excel_export():
    """Test the Excel exporter with sample data"""
    from win_loss_report_generator import WinLossReportGenerator
    
    # Generate sample report data
    generator = WinLossReportGenerator(client_id="Supio")
    themes_data = generator.generate_analyst_report()
    
    if themes_data["success"]:
        # Export to Excel
        exporter = ExcelWinLossExporter()
        output_file = exporter.export_analyst_workbook(themes_data)
        print(f"✅ Excel workbook created: {output_file}")
        return output_file
    else:
        print(f"❌ Error generating themes: {themes_data['error']}")
        return None

if __name__ == "__main__":
    test_excel_export() 