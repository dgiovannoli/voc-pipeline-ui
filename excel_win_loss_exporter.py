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
from typing import Dict, List, Any, Tuple
import xlsxwriter
from collections import defaultdict
import json

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
        self.db = None
        self.client_id = None
        self.discussion_guide = None
        # Navigation mappings for internal links
        self.raw_data_q_first_row = {}
        self.raw_data_q_companies = {}
        self.raw_data_q_quotes = {}
        self.themes_q_first_row = {}
        self.themes_list_by_question = {}
        self.question_responses_first_row = {}
        self.research_themes_first_row = {}
        self.research_theme_row_by_id = {}
        self.discovered_theme_row_by_id = {}
        self.question_map = {}
        self.quotes_df = None
        
    def export_analyst_workbook(self, themes_data: Dict[str, Any], output_path: str = None, unified: bool = False) -> str:
        """
        Export complete analyst curation workbook.
        
        Args:
            themes_data: Output from WinLossReportGenerator
            output_path: Optional custom output path
            unified: If True, emit a single 'Themes' sheet using the Win Drivers layout and skip section tabs
            
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
        
        # Initialize database connection
        from supabase_database import SupabaseDatabase
        self.db = SupabaseDatabase()
        self.client_id = themes_data["metadata"]["client_id"]
        
        # Create workbook and define formatting
        self.workbook = xlsxwriter.Workbook(output_path)
        self._define_formats()
        
        try:
            # Load discussion guide if available
            try:
                from discussion_guide_integration import DiscussionGuideIntegrator
                integrator = DiscussionGuideIntegrator()
                discussion_guide_data = integrator.parse_supio_discussion_guide('uploads/Supio_PRJ-00027 Discussion Guide v1.txt')
                self.discussion_guide = discussion_guide_data.get('questions', []) if discussion_guide_data else []
                # Dedupe near-identical guide questions by normalization to avoid split blocks
                def _dg_key(q: str) -> str:
                    qn = (q or '').strip().lower()
                    qn = ''.join(ch for ch in qn if ch.isalnum() or ch.isspace())
                    return ' '.join(qn.split())
                seen_keys = {}
                deduped = []
                self._guide_canonical_map = {}
                for q in self.discussion_guide:
                    k = _dg_key(q)
                    if k in seen_keys:
                        # map duplicate to first canonical
                        self._guide_canonical_map[q] = seen_keys[k]
                        continue
                    seen_keys[k] = q
                    self._guide_canonical_map[q] = q
                    deduped.append(q)
                if len(deduped) != len(self.discussion_guide):
                    logger.info(f"🔁 Deduped discussion guide: {len(self.discussion_guide)} → {len(deduped)}")
                self.discussion_guide = deduped
                logger.info(f"✅ Loaded discussion guide with {len(self.discussion_guide)} questions")
            except Exception as e:
                logger.warning(f"⚠️ Could not load discussion guide: {e}")
                self.discussion_guide = []
            
            # In unified fast path, put Research Question Coverage first per request
            # Otherwise keep Executive Summary first
            if not unified:
                self._create_executive_summary_tab(themes_data, unified=unified)
            
            # Cache quotes df if present in curation data (optional)
            try:
                if 'curation_data' in themes_data and isinstance(themes_data['curation_data'], dict):
                    # Not always present; safe best-effort
                    pass
            except Exception:
                pass
            
            if unified:
                # Fast path: minimal workbook
                # 1) All Themes (unified review list)
                try:
                    self._create_all_themes_tab(themes_data)
                except Exception:
                    pass
                # 2) Research Themes (guide-seeded)
                self._create_research_question_coverage_tab(themes_data)
                # 3) Discovered Themes (cross-interview patterns by harmonized subjects)
                self._create_discovered_themes_tab(themes_data)
                # 4) Mapping QA tab for analyst overrides (review-only)
                self._create_mapping_qa_tab(themes_data)
                # 5) Raw Data reference at the end
                self._create_raw_data_tab(themes_data)
            else:
                # Tab 2: Research Question Coverage
                self._create_research_question_coverage_tab(themes_data)
                
                # Tab 3: Win Drivers Section Validation
                self._create_win_drivers_validation_tab(themes_data)
                
                # Tab 4: Loss Factors Section Validation
                self._create_loss_factors_validation_tab(themes_data)
                
                # Tab 5: Competitive Intelligence Section Validation
                self._create_competitive_intelligence_validation_tab(themes_data)
                
                # Tab 6: Implementation Insights Section Validation
                self._create_implementation_insights_validation_tab(themes_data)
                
                # Tab 7: Pricing Analysis Section
                self._create_pricing_analysis_tab(themes_data)
                
                # Tab 8: Section Planning Dashboard (Optional overview)
                self._create_section_planning_tab(themes_data)
                
                # Tab 9: Raw Data Reference
                self._create_raw_data_tab(themes_data)
                
                # Tab 10: Cross-Section Themes Reference
                self._create_cross_section_reference_tab(themes_data)
                
                # Tab 11: Report Builder Template
                self._create_unified_report_builder_tab(themes_data)
                
                # Tab 12: Report Outline Generator (for detailed structure)
                self._create_report_outline_generator_tab(themes_data)
            
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
            }),
            'validated': self.workbook.add_format({
                'bg_color': '#90EE90', 'font_color': '#006400', 'bold': True, 'align': 'center'
            }),
            'pending': self.workbook.add_format({
                'bg_color': '#FFD700', 'font_color': '#8B4513', 'bold': True, 'align': 'center'
            })
        }
    
    def _create_executive_summary_tab(self, themes_data: Dict[str, Any], unified: bool = False):
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
        
        # Discussion Guide Integration section
        row += 2
        worksheet.write(row, 0, "Discussion Guide Integration", self.formats['subheader'])
        row += 1
        
        # Check if discussion guide is available
        discussion_guide = getattr(self, 'discussion_guide', None)
        if discussion_guide and len(discussion_guide) > 0 and not unified:
            worksheet.write(row, 0, "✅ Discussion Guide Connected:", self.formats['strength'])
            worksheet.write(row, 1, f"{len(discussion_guide)} research questions loaded")
            row += 1
            
            # Live formulas referencing the integrated coverage tab
            # Coverage: =B7 & "/" & B6 & " (" & B8 & ")" from 'Research Question Coverage'
            worksheet.write(row, 0, "📊 Coverage:", self.formats['data_cell'])
            coverage_formula = "='Research Question Coverage'!B7 & \"/\" & 'Research Question Coverage'!B6 & \" (\" & 'Research Question Coverage'!B8 & \")\""
            worksheet.write_formula(row, 1, coverage_formula, self.formats['data_cell'])
            row += 1
            
            # Uncovered questions list (uses TEXTJOIN+FILTER over question rows starting at row 11)
            worksheet.write(row, 0, "⚠️ Uncovered Questions:", self.formats['data_cell'])
            uncovered_formula = "=IFERROR(TEXTJOIN(\", \", TRUE, FILTER('Research Question Coverage'!A11:A1000, 'Research Question Coverage'!D11:D1000=\"❌ UNCOVERED\")), \"None\")"
            worksheet.write_formula(row, 1, uncovered_formula, self.formats['data_cell'])
            row += 1
            
            worksheet.write(row, 0, "📋 Details:", self.formats['data_cell'])
            worksheet.write(row, 1, "See 'Research Question Coverage' tab for integrated view (Research + Discovered)")
            row += 1
        else:
            # In unified mode, we omit coverage references entirely
            if not unified:
                worksheet.write(row, 0, "⚠️ No Discussion Guide Connected", self.formats['weakness'])
                worksheet.write(row, 1, "Upload discussion guide for better research alignment")
            row += 1
        
        # Key recommendations section
        row += 2
        worksheet.write(row, 0, "Analyst Action Items", self.formats['subheader'])
        row += 1
        
        recommendations = [
            ("1. Review unified Themes tab - approve/reject themes and assign report sections" if unified else "1. Review section validation tabs - approve/reject themes for final report"),
            ("2. Classify quotes as FEATURED/PRIMARY/SUPPORTING/EXCLUDE in Themes tab" if unified else "2. Classify quotes as FEATURED/PRIMARY/SUPPORTING/EXCLUDE in each section"), 
            ("3. Build final report using Report Builder tab"),
            ("4. Cross-reference Raw Data for additional context when needed")
        ]
        
        for rec in recommendations:
            worksheet.write(row, 0, rec, self.formats['data_cell'])
            row += 1
    
    def _create_coverage_validation_tab(self, themes_data: Dict[str, Any]):
        """Phase 1: Discussion Guide Coverage - Map research questions to discovered themes"""
        worksheet = self.workbook.add_worksheet('Phase 1 - Coverage')
        
        # Set column widths
        worksheet.set_column('A:A', 50)  # Research Question
        worksheet.set_column('B:B', 40)  # Related Discovered Themes
        worksheet.set_column('C:C', 20)  # Coverage Assessment
        worksheet.set_column('D:D', 15)  # Theme Count
        worksheet.set_column('E:E', 15)  # Quote Count
        worksheet.set_column('F:F', 50)  # Coverage Notes
        worksheet.set_column('G:G', 20)  # Action Needed
        
        # Title and instructions
        worksheet.merge_range('A1:G1', "Phase 1: Discussion Guide Coverage Validation", self.formats['title'])
        worksheet.merge_range('A2:G2', "PURPOSE: Validate that discovered themes address your original research questions. Add your discussion guide questions below, then assess coverage.", self.formats['subheader'])
        
        # Headers
        headers = [
            "Original Research Question", "Related Discovered Themes", "Coverage Assessment",
            "Theme Count", "Quote Count", "Coverage Notes", "Action Needed"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Instructions for analyst to fill in research questions
        row = 4
        
        # Sample research questions with mapping to discovered themes
        sample_questions = self._generate_sample_research_questions(themes_data['themes'])
        
        for question_data in sample_questions:
            # Research Question
            worksheet.write(row, 0, question_data['question'], self.formats['data_cell'])
            
            # Related Themes (discovered)
            related_themes = "; ".join(question_data['related_themes'][:3])
            if len(question_data['related_themes']) > 3:
                related_themes += f" (+{len(question_data['related_themes']) - 3} more)"
            worksheet.write(row, 1, related_themes, self.formats['data_cell'])
            
            # Coverage Assessment dropdown
            worksheet.data_validation(row, 2, row, 2, {
                'validate': 'list',
                'source': ['STRONG - Well covered', 'ADEQUATE - Sufficient', 'WEAK - Limited coverage', 'MISSING - No themes found', 'REVIEW NEEDED']
            })
            worksheet.write(row, 2, question_data['coverage'], self.formats['decision_cell'])
            
            # Theme Count
            worksheet.write(row, 3, len(question_data['related_themes']), self.formats['number'])
            
            # Quote Count
            worksheet.write(row, 4, question_data['quote_count'], self.formats['number'])
            
            # Coverage Notes
            worksheet.write(row, 5, "", self.formats['notes_cell'])
            
            # Action Needed dropdown
            worksheet.data_validation(row, 6, row, 6, {
                'validate': 'list',
                'source': ['COMPLETE', 'FOLLOW UP NEEDED', 'SUPPLEMENTAL RESEARCH', 'REFRAME QUESTION']
            })
            worksheet.write(row, 6, "", self.formats['decision_cell'])
            
            row += 1
        
        # Add blank rows for additional research questions
        for i in range(5):
            worksheet.write(row, 0, "[ADD YOUR RESEARCH QUESTION HERE]", self.formats['notes_cell'])
            worksheet.data_validation(row, 2, row, 2, {
                'validate': 'list',
                'source': ['STRONG - Well covered', 'ADEQUATE - Sufficient', 'WEAK - Limited coverage', 'MISSING - No themes found', 'REVIEW NEEDED']
            })
            worksheet.data_validation(row, 6, row, 6, {
                'validate': 'list',
                'source': ['COMPLETE', 'FOLLOW UP NEEDED', 'SUPPLEMENTAL RESEARCH', 'REFRAME QUESTION']
            })
            row += 1
        
        # Add summary
        row += 2
        worksheet.write(row, 0, "COVERAGE SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Discovered Themes: {len(themes_data['themes'])}")
        worksheet.write(row, 2, "Research Questions Covered: [TO BE DETERMINED]")
        worksheet.write(row, 4, "Coverage Confidence: [RATE 1-5]")

    def _generate_sample_research_questions(self, themes: List[Dict[str, Any]]) -> List[Dict]:
        """Generate sample research questions mapped to discovered themes"""
        # Group themes by subject for mapping
        themes_by_subject = {}
        for theme in themes:
            subject = theme.get('harmonized_subject', 'Unknown')
            if subject not in themes_by_subject:
                themes_by_subject[subject] = []
            themes_by_subject[subject].append(theme.get('theme_title', theme.get('theme_id', 'Unknown')))
        
        # Create sample questions based on common VOC research areas
        sample_questions = []
        
        # Map subjects to research questions
        subject_to_question = {
            'Product Capabilities': "What product features drive vendor selection decisions?",
            'Pricing and Commercial': "How do pricing models influence purchase decisions?", 
            'Implementation Process': "What implementation challenges affect vendor satisfaction?",
            'Sales Experience': "How does the sales process impact vendor perception?",
            'User Experience': "What usability factors influence user adoption?",
            'Competitive Dynamics': "How do vendors compare in the competitive landscape?",
            'Market Discovery': "What market needs are driving vendor evaluation?",
            'Support and Service': "How does ongoing support affect vendor relationships?",
            'Integration Technical': "What technical requirements drive integration decisions?",
            'Vendor Stability': "How important is vendor stability in selection decisions?"
        }
        
        for subject, question in subject_to_question.items():
            if subject in themes_by_subject:
                related_themes = themes_by_subject[subject]
                # Estimate coverage based on number of themes
                if len(related_themes) >= 3:
                    coverage = "STRONG - Well covered"
                elif len(related_themes) >= 2:
                    coverage = "ADEQUATE - Sufficient"
                else:
                    coverage = "WEAK - Limited coverage"
                
                sample_questions.append({
                    'question': question,
                    'related_themes': related_themes,
                    'coverage': coverage,
                    'quote_count': len(related_themes) * 8  # Rough estimate
                })
        
        return sample_questions[:8]  # Limit to top 8 questions

    def _create_win_drivers_validation_tab(self, themes_data: Dict[str, Any]):
        """Win Drivers Section Validation - Integrated theme and quote validation"""
        worksheet = self.workbook.add_worksheet('Win Drivers Section')
        
        # Set column widths for integrated validation
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 15)  # Theme Origin
        worksheet.set_column('D:D', 20)  # Report Section
        worksheet.set_column('E:E', 30)  # Research Question
        worksheet.set_column('F:F', 40)  # Verbatim Question (DB)
        worksheet.set_column('G:G', 60)  # Quote Text
        worksheet.set_column('H:H', 15)  # Company
        worksheet.set_column('I:I', 15)  # Interviewee
        worksheet.set_column('J:J', 12)  # Sentiment
        worksheet.set_column('K:K', 12)  # Impact Score
        worksheet.set_column('L:L', 15)  # Deal Status
        worksheet.set_column('M:M', 25)  # Quote Classification
        worksheet.set_column('N:N', 25)  # Theme Decision
        worksheet.set_column('O:O', 40)  # Analyst Notes
        
        # Title and instructions
        worksheet.merge_range('A1:O1', "Win Drivers Section Validation", self.formats['title'])
        worksheet.merge_range('A2:O2', "PURPOSE: Validate themes and quotes for the 'Why You Win' section. See how each theme contributes to the win story.", self.formats['subheader'])
        
        # Section context
        worksheet.merge_range('A3:O3', "📖 SECTION CONTEXT: This section explains why customers choose your solution over competitors. Focus on strengths, capabilities, and positive differentiators.", self.formats['data_cell'])
        
        # Research question context
        worksheet.merge_range('A4:O4', "🔍 RESEARCH FOCUS: 'What product features and capabilities drive vendor selection decisions?' 'What do customers value most about our solution?'", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Theme Origin", "Report Section", "Research Question", 
            "Verbatim Question (DB)", "Quote Text", "Company", "Interviewee", "Sentiment", "Impact Score", "Deal Status", "Quote Classification", "Theme Decision", "Analyst Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, self.formats['header'])
        
        # Process win driver themes - one quote per row
        row = 6
        win_themes = self._filter_themes_by_section(themes_data['themes'], 'win')
        
        # Get cross-section map to avoid duplication
        cross_section_map = self._identify_cross_section_themes(themes_data['themes'])
        
        # Include ALL win themes, regardless of primary section
        # This allows analysts to make decisions about where themes belong
        primary_win_themes = win_themes
        
        for theme in primary_win_themes:
            all_quotes = theme.get('all_quotes', [])
            theme_id = theme.get('theme_id', 'unknown')
            
            # Check if this is a cross-section theme
            is_cross_section = theme_id in cross_section_map
            cross_sections = cross_section_map.get(theme_id, [])
            
            # Write theme info for first quote only
            first_quote = True
            
            for quote in all_quotes:
                # Theme info (only for first quote of each theme)
                if first_quote:
                    worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
                    
                    # Add cross-reference info to theme statement if it's a cross-section theme
                    theme_statement = theme.get('theme_statement', 'No statement generated')
                    if is_cross_section:
                        other_sections = [s for s in cross_sections if s != 'win']
                        theme_statement += f" [CROSS-SECTION: Also appears in {', '.join(other_sections).title()}]"
                    
                    worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
                    
                    # Theme Origin (new 3rd column)
                    worksheet.write(row, 2, theme.get('theme_origin', 'discovered').title(), self.formats['data_cell'])
                    
                    worksheet.write(row, 3, "Win Drivers", self.formats['data_cell'])
                    worksheet.write(row, 4, self._map_theme_to_research_question(theme), self.formats['data_cell'])
                    worksheet.write(row, 5, quote.get('question', ''), self.formats['data_cell'])
                    worksheet.write(row, 6, quote.get('verbatim_response', 'No quote text'), self.formats['data_cell'])
                    worksheet.write(row, 7, quote.get('company', quote.get('company_name', 'Unknown')), self.formats['data_cell'])
                    worksheet.write(row, 8, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                    worksheet.write(row, 9, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                    worksheet.write(row, 10, quote.get('impact_score', 0), self.formats['number'])
                    
                    # Deal Status
                    deal_status = quote.get('deal_status', 'Unknown')
                    # Format deal status for better readability
                    if deal_status:
                        if 'won' in deal_status.lower():
                            formatted_status = "WON"
                        elif 'lost' in deal_status.lower():
                            formatted_status = "LOST"
                        else:
                            formatted_status = deal_status.upper()
                    else:
                        formatted_status = "UNKNOWN"
                    worksheet.write(row, 11, formatted_status, self.formats['data_cell'])
                    
                    # Quote Classification dropdown
                    worksheet.data_validation(row, 12, row, 12, {
                        'validate': 'list',
                        'source': ['FEATURED - Executive summary', 'PRIMARY - Main evidence', 'SUPPORTING - Background', 'EXCLUDE - Do not use']
                    })
                    worksheet.write(row, 12, "", self.formats['decision_cell'])
                    
                    # Theme Decision dropdown
                    worksheet.data_validation(row, 13, row, 13, {
                        'validate': 'list',
                        'source': ['VALIDATED - Use in report', 'REJECTED - Insufficient evidence', 'REVISED - Needs statement changes', 'MERGE - Combine with other theme']
                    })
                    worksheet.write(row, 13, "", self.formats['decision_cell'])
                    
                    # Analyst Notes
                    worksheet.write(row, 14, "", self.formats['notes_cell'])
                    
                    row += 1
                
                # Individual quote data (shifted by +1 from previous layout)
                worksheet.write(row, 0, "", self.formats['data_cell'])
                worksheet.write(row, 1, "", self.formats['data_cell'])
                worksheet.write(row, 2, "", self.formats['data_cell'])
                worksheet.write(row, 3, "", self.formats['data_cell'])
                worksheet.write(row, 4, "", self.formats['data_cell'])
                worksheet.write(row, 5, "", self.formats['data_cell'])
                worksheet.write(row, 6, "", self.formats['data_cell'])
                worksheet.write(row, 7, "", self.formats['data_cell'])
                worksheet.write(row, 8, "", self.formats['data_cell'])
                worksheet.write(row, 9, "", self.formats['data_cell'])
                worksheet.write(row, 10, "", self.formats['data_cell'])
                worksheet.write(row, 11, "", self.formats['data_cell'])
                worksheet.write(row, 12, "", self.formats['data_cell'])
                worksheet.write(row, 13, "", self.formats['data_cell'])
                worksheet.write(row, 14, "", self.formats['data_cell'])
                
                row += 1
            
            # Add Theme Decision Row after all quotes for this theme
            worksheet.write(row, 0, f"THEME DECISION: {theme['theme_id']}", self.formats['header'])
            worksheet.write(row, 1, "After reviewing all quotes above, make theme decision:", self.formats['subheader'])
            
            # Theme Decision dropdown
            worksheet.data_validation(row, 13, row, 13, {
                'validate': 'list',
                'source': ['PENDING REVIEW', 'VALIDATED - Include in Report', 'REJECTED - Exclude from Report', 'NEEDS REVISION', 'FEATURED - Highlight in Executive Summary']
            })
            worksheet.write(row, 13, "PENDING REVIEW", self.formats['pending'])
            
            # Theme-level analyst notes
            worksheet.write(row, 14, "", self.formats['notes_cell'])
            
            row += 1
            
            # Add a blank row between themes for visual separation
            row += 1
        
        # Add section summary
        row += 2
        worksheet.write(row, 0, "WIN DRIVERS SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Win Themes: {len(win_themes)}")
        worksheet.write(row, 3, "Validated Themes: [Count after review]")
        worksheet.write(row, 6, "Featured Quotes: [Count]")

    def _create_loss_factors_validation_tab(self, themes_data: Dict[str, Any]):
        """Loss Factors Section Validation - Integrated theme and quote validation"""
        worksheet = self.workbook.add_worksheet('Loss Factors Section')
        
        # Set column widths for integrated validation
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 15)  # Theme Origin
        worksheet.set_column('D:D', 20)  # Report Section
        worksheet.set_column('E:E', 30)  # Research Question
        worksheet.set_column('F:F', 40)  # Verbatim Question (DB)
        worksheet.set_column('G:G', 60)  # Quote Text
        worksheet.set_column('H:H', 15)  # Company
        worksheet.set_column('I:I', 15)  # Interviewee
        worksheet.set_column('J:J', 12)  # Sentiment
        worksheet.set_column('K:K', 12)  # Impact Score
        worksheet.set_column('L:L', 15)  # Deal Status
        worksheet.set_column('M:M', 25)  # Quote Classification
        worksheet.set_column('N:N', 25)  # Theme Decision
        worksheet.set_column('O:O', 40)  # Analyst Notes
        
        # Title and instructions
        worksheet.merge_range('A1:O1', "Loss Factors Section Validation", self.formats['title'])
        worksheet.merge_range('A2:O2', "PURPOSE: Validate themes and quotes for the 'Why You Lose' section. Identify areas for improvement and competitive gaps.", self.formats['subheader'])
        
        # Section context
        worksheet.merge_range('A3:O3', "📖 SECTION CONTEXT: This section explains why customers choose competitors or don't select your solution. Focus on weaknesses, gaps, and areas for improvement.", self.formats['data_cell'])
        
        # Research question context
        worksheet.merge_range('A4:O4', "🔍 RESEARCH FOCUS: 'What factors lead to lost deals?' 'What do customers see as our weaknesses?' 'What competitive advantages do others have?'", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Theme Origin", "Report Section", "Research Question", 
            "Verbatim Question (DB)", "Quote Text", "Company", "Interviewee", "Sentiment", "Impact Score", "Deal Status", "Quote Classification", "Theme Decision", "Analyst Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, self.formats['header'])
        
        # Process loss factor themes - one quote per row
        row = 6
        loss_themes = self._filter_themes_by_section(themes_data['themes'], 'loss')
        
        # Get cross-section map to avoid duplication
        cross_section_map = self._identify_cross_section_themes(themes_data['themes'])
        
        # Include ALL loss themes, regardless of primary section
        # This allows analysts to make decisions about where themes belong
        primary_loss_themes = loss_themes
        
        for theme in primary_loss_themes:
            all_quotes = theme.get('all_quotes', [])
            theme_id = theme.get('theme_id', 'unknown')
            
            # Check if this is a cross-section theme
            is_cross_section = theme_id in cross_section_map
            cross_sections = cross_section_map.get(theme_id, [])
            
            # Write theme info for first quote only
            first_quote = True
            
            for quote in all_quotes:
                # Theme info (only show for first quote of each theme)
                if first_quote:
                    worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
                    
                    # Add cross-reference info to theme statement if it's a cross-section theme
                    theme_statement = theme.get('theme_statement', 'No statement generated')
                    if is_cross_section:
                        other_sections = [s for s in cross_sections if s != 'loss']
                        theme_statement += f" [CROSS-SECTION: Also appears in {', '.join(other_sections).title()}]"
                    
                    worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
                    
                    # Theme Origin (new 3rd column)
                    worksheet.write(row, 2, theme.get('theme_origin', 'discovered').title(), self.formats['data_cell'])
                    
                    worksheet.write(row, 3, "Loss Factors", self.formats['data_cell'])
                    worksheet.write(row, 4, self._map_theme_to_research_question(theme), self.formats['data_cell'])
                    worksheet.write(row, 5, quote.get('question', ''), self.formats['data_cell'])
                    worksheet.write(row, 6, quote.get('verbatim_response', 'No quote text'), self.formats['data_cell'])
                    worksheet.write(row, 7, quote.get('company', quote.get('company_name', 'Unknown')), self.formats['data_cell'])
                    worksheet.write(row, 8, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                    worksheet.write(row, 9, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                    worksheet.write(row, 10, quote.get('impact_score', 0), self.formats['number'])
                    
                    # Deal Status
                    deal_status = quote.get('deal_status', 'Unknown')
                    if deal_status:
                        if 'won' in deal_status.lower():
                            formatted_status = "WON"
                        elif 'lost' in deal_status.lower():
                            formatted_status = "LOST"
                        else:
                            formatted_status = deal_status.upper()
                    else:
                        formatted_status = "UNKNOWN"
                    worksheet.write(row, 11, formatted_status, self.formats['data_cell'])
                    
                    # Quote Classification dropdown
                    worksheet.data_validation(row, 12, row, 12, {
                        'validate': 'list',
                        'source': ['FEATURED - Executive summary', 'PRIMARY - Main evidence', 'SUPPORTING - Background', 'EXCLUDE - Do not use']
                    })
                    worksheet.write(row, 12, "", self.formats['decision_cell'])
                    
                    # Theme Decision dropdown
                    worksheet.data_validation(row, 13, row, 13, {
                        'validate': 'list',
                        'source': ['VALIDATED - Use in report', 'REJECTED - Insufficient evidence', 'REVISED - Needs statement changes', 'MERGE - Combine with other theme']
                    })
                    worksheet.write(row, 13, "", self.formats['decision_cell'])
                    
                    # Analyst Notes
                    worksheet.write(row, 14, "", self.formats['notes_cell'])
                    
                    row += 1
                
                # Individual quote data (shifted by +1)
                worksheet.write(row, 0, "", self.formats['data_cell'])
                worksheet.write(row, 1, "", self.formats['data_cell'])
                worksheet.write(row, 2, "", self.formats['data_cell'])
                worksheet.write(row, 3, "", self.formats['data_cell'])
                worksheet.write(row, 4, "", self.formats['data_cell'])
                worksheet.write(row, 5, "", self.formats['data_cell'])
                worksheet.write(row, 6, "", self.formats['data_cell'])
                worksheet.write(row, 7, "", self.formats['data_cell'])
                worksheet.write(row, 8, "", self.formats['data_cell'])
                worksheet.write(row, 9, "", self.formats['data_cell'])
                worksheet.write(row, 10, "", self.formats['data_cell'])
                worksheet.write(row, 11, "", self.formats['data_cell'])
                worksheet.write(row, 12, "", self.formats['data_cell'])
                worksheet.write(row, 13, "", self.formats['data_cell'])
                worksheet.write(row, 14, "", self.formats['data_cell'])
                
                row += 1
            
            # Add Theme Decision Row after all quotes for this theme
            worksheet.write(row, 0, f"THEME DECISION: {theme['theme_id']}", self.formats['header'])
            worksheet.write(row, 1, "After reviewing all quotes above, make theme decision:", self.formats['subheader'])
            
            # Theme Decision dropdown
            worksheet.data_validation(row, 13, row, 13, {
                'validate': 'list',
                'source': ['PENDING REVIEW', 'VALIDATED - Include in Report', 'REJECTED - Exclude from Report', 'NEEDS REVISION', 'FEATURED - Highlight in Executive Summary']
            })
            worksheet.write(row, 13, "PENDING REVIEW", self.formats['pending'])
            
            # Theme-level analyst notes
            worksheet.write(row, 14, "", self.formats['notes_cell'])
            
            row += 1
            
            # Add a blank row between themes for visual separation
            row += 1
        
        # Add section summary
        row += 2
        worksheet.write(row, 0, "LOSS FACTORS SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Loss Themes: {len(loss_themes)}")
        worksheet.write(row, 3, "Validated Themes: [Count after review]")
        worksheet.write(row, 6, "Featured Quotes: [Count]")

    def _create_competitive_intelligence_validation_tab(self, themes_data: Dict[str, Any]):
        """Competitive Intelligence Section Validation - Integrated theme and quote validation"""
        worksheet = self.workbook.add_worksheet('Competitive Intelligence')
        
        # Set column widths for integrated validation
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 20)  # Report Section
        worksheet.set_column('D:D', 30)  # Research Question
        worksheet.set_column('E:E', 60)  # Verbatim Question (DB)
        worksheet.set_column('F:F', 40)  # Quote Text
        worksheet.set_column('G:G', 15)  # Company
        worksheet.set_column('H:H', 15)  # Interviewee
        worksheet.set_column('I:I', 12)  # Sentiment
        worksheet.set_column('J:J', 12)  # Impact Score
        worksheet.set_column('K:K', 25)  # Quote Classification
        worksheet.set_column('L:L', 25)  # Theme Decision
        worksheet.set_column('M:M', 40)  # Analyst Notes
        
        # Title and instructions
        worksheet.merge_range('A1:M1', "Competitive Intelligence Section Validation", self.formats['title'])
        worksheet.merge_range('A2:M2', "PURPOSE: Validate themes and quotes for competitive analysis. Understand how customers view competitors vs. your solution.", self.formats['subheader'])
        
        # Section context
        worksheet.merge_range('A3:M3', "📖 SECTION CONTEXT: This section provides insights into competitive positioning, market dynamics, and how customers compare solutions.", self.formats['data_cell'])
        
        # Research question context
        worksheet.merge_range('A4:M4', "🔍 RESEARCH FOCUS: 'How do customers compare vendors?' 'What competitive advantages do others have?' 'What market dynamics affect decisions?'", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Report Section", "Research Question", 
            "Verbatim Question (DB)", "Quote Text", "Company", "Interviewee", "Sentiment", "Impact Score", "Quote Classification", "Theme Decision", "Analyst Notes", "Theme Origin"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, self.formats['header'])
        
        # Process competitive themes - one quote per row
        row = 6
        competitive_themes = self._filter_themes_by_section(themes_data['themes'], 'competitive')
        
        # Get cross-section map to avoid duplication
        cross_section_map = self._identify_cross_section_themes(themes_data['themes'])
        
        # Include ALL competitive themes, regardless of primary section
        # This allows analysts to make decisions about where themes belong
        primary_competitive_themes = competitive_themes
        
        for theme in primary_competitive_themes:
            all_quotes = theme.get('all_quotes', [])
            theme_id = theme.get('theme_id', 'unknown')
            
            # Check if this is a cross-section theme
            is_cross_section = theme_id in cross_section_map
            cross_sections = cross_section_map.get(theme_id, [])
            
            # Write theme info for first quote only
            first_quote = True
            
            for quote in all_quotes:
                # Theme ID (only show for first quote of each theme)
                if first_quote:
                    worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
                    
                    # Add cross-reference info to theme statement if it's a cross-section theme
                    theme_statement = theme.get('theme_statement', 'No statement generated')
                    if is_cross_section:
                        other_sections = [s for s in cross_sections if s != 'competitive']
                        theme_statement += f" [CROSS-SECTION: Also appears in {', '.join(other_sections).title()}]"
                    
                    worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
                    worksheet.write(row, 2, "Competitive Intelligence", self.formats['data_cell'])
                    worksheet.write(row, 3, self._map_theme_to_research_question(theme), self.formats['data_cell'])
                    worksheet.write(row, 4, quote.get('question', ''), self.formats['data_cell'])
                    worksheet.write(row, 5, quote.get('verbatim_response', 'No quote text'), self.formats['data_cell'])
                    worksheet.write(row, 6, quote.get('company', quote.get('company_name', 'Unknown')), self.formats['data_cell'])
                    worksheet.write(row, 7, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                    worksheet.write(row, 8, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                    worksheet.write(row, 9, quote.get('impact_score', 0), self.formats['number'])
                    
                    # Quote Classification dropdown
                    worksheet.data_validation(row, 10, row, 10, {
                        'validate': 'list',
                        'source': ['FEATURED - Key competitive insight', 'PRIMARY - Main competitive evidence', 'SUPPORTING - Background competitive context', 'EXCLUDE - Do not use']
                    })
                    worksheet.write(row, 10, "", self.formats['decision_cell'])
                    
                    # Theme Decision (only for first quote of each theme)
                    if first_quote or row == 6:  # First quote of first theme
                        worksheet.data_validation(row, 11, row, 11, {
                            'validate': 'list',
                            'source': ['VALIDATED - Use in report', 'REJECTED - Insufficient evidence', 'REVISED - Needs statement changes', 'MERGE - Combine with other theme']
                        })
                        worksheet.write(row, 11, "", self.formats['decision_cell'])
                    else:
                        worksheet.write(row, 11, "", self.formats['data_cell'])
                    
                    # Analyst Notes
                    worksheet.write(row, 12, "", self.formats['notes_cell'])
                    
                    # Theme Origin column (first quote row only)
                    worksheet.write(row, 13, theme.get('theme_origin', 'discovered').title(), self.formats['data_cell'])
                    
                    row += 1
                
                # Individual quote data
                worksheet.write(row, 0, "", self.formats['data_cell'])
                worksheet.write(row, 1, "", self.formats['data_cell'])
                worksheet.write(row, 2, "", self.formats['data_cell'])
                worksheet.write(row, 3, "", self.formats['data_cell'])
                worksheet.write(row, 4, "", self.formats['data_cell'])
                worksheet.write(row, 5, "", self.formats['data_cell'])
                worksheet.write(row, 6, "", self.formats['data_cell'])
                worksheet.write(row, 7, "", self.formats['data_cell'])
                worksheet.write(row, 8, "", self.formats['data_cell'])
                worksheet.write(row, 9, "", self.formats['data_cell'])
                worksheet.write(row, 10, "", self.formats['data_cell'])
                worksheet.write(row, 11, "", self.formats['data_cell'])
                worksheet.write(row, 12, "", self.formats['data_cell'])
                worksheet.write(row, 13, "", self.formats['data_cell'])
                worksheet.write(row, 14, "", self.formats['data_cell'])
                
                row += 1
            
            # Add a blank row between themes for visual separation
            row += 1
        
        # Add section summary
        row += 2
        worksheet.write(row, 0, "COMPETITIVE INTELLIGENCE SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Competitive Themes: {len(competitive_themes)}")
        worksheet.write(row, 3, "Validated Themes: [Count after review]")
        worksheet.write(row, 6, "Featured Quotes: [Count]")

    def _create_implementation_insights_validation_tab(self, themes_data: Dict[str, Any]):
        """Implementation Insights Section Validation - Integrated theme and quote validation"""
        worksheet = self.workbook.add_worksheet('Implementation Insights')
        
        # Set column widths for integrated validation
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 20)  # Report Section
        worksheet.set_column('D:D', 30)  # Research Question
        worksheet.set_column('E:E', 60)  # Verbatim Question (DB)
        worksheet.set_column('F:F', 40)  # Quote Text
        worksheet.set_column('G:G', 15)  # Company
        worksheet.set_column('H:H', 15)  # Interviewee
        worksheet.set_column('I:I', 12)  # Sentiment
        worksheet.set_column('J:J', 12)  # Impact Score
        worksheet.set_column('K:K', 25)  # Quote Classification
        worksheet.set_column('L:L', 25)  # Theme Decision
        worksheet.set_column('M:M', 40)  # Analyst Notes
        
        # Title and instructions
        worksheet.merge_range('A1:M1', "Implementation Insights Section Validation", self.formats['title'])
        worksheet.merge_range('A2:M2', "PURPOSE: Validate themes and quotes for implementation insights. Understand deployment challenges and success factors.", self.formats['subheader'])
        
        # Section context
        worksheet.merge_range('A3:M3', "📖 SECTION CONTEXT: This section covers implementation experiences, deployment challenges, and factors that affect successful adoption.", self.formats['data_cell'])
        
        # Research question context
        worksheet.merge_range('A4:M4', "🔍 RESEARCH FOCUS: 'What implementation challenges do customers face?' 'What factors drive successful deployment?' 'How does implementation affect satisfaction?'", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Report Section", "Research Question", 
            "Verbatim Question (DB)", "Quote Text", "Company", "Interviewee", "Sentiment", "Impact Score", "Quote Classification", "Theme Decision", "Analyst Notes", "Theme Origin"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, self.formats['header'])
        
        # Process implementation themes - one quote per row
        row = 6
        implementation_themes = self._filter_themes_by_section(themes_data['themes'], 'implementation')
        
        # Get cross-section map to avoid duplication
        cross_section_map = self._identify_cross_section_themes(themes_data['themes'])
        
        # Include ALL implementation themes, regardless of primary section
        # This allows analysts to make decisions about where themes belong
        primary_implementation_themes = implementation_themes
        
        for theme in primary_implementation_themes:
            all_quotes = theme.get('all_quotes', [])
            theme_id = theme.get('theme_id', 'unknown')
            
            # Check if this is a cross-section theme
            is_cross_section = theme_id in cross_section_map
            cross_sections = cross_section_map.get(theme_id, [])
            
            # Write theme info for first quote only
            first_quote = True
            
            for quote in all_quotes:
                # Theme ID (only show for first quote of each theme)
                if first_quote:
                    worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
                    
                    # Add cross-reference info to theme statement if it's a cross-section theme
                    theme_statement = theme.get('theme_statement', 'No statement generated')
                    if is_cross_section:
                        other_sections = [s for s in cross_sections if s != 'implementation']
                        theme_statement += f" [CROSS-SECTION: Also appears in {', '.join(other_sections).title()}]"
                    
                    worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
                    worksheet.write(row, 2, "Implementation Insights", self.formats['data_cell'])
                    worksheet.write(row, 3, self._map_theme_to_research_question(theme), self.formats['data_cell'])
                    worksheet.write(row, 4, quote.get('question', ''), self.formats['data_cell'])
                    worksheet.write(row, 5, quote.get('verbatim_response', 'No quote text'), self.formats['data_cell'])
                    worksheet.write(row, 6, quote.get('company', quote.get('company_name', 'Unknown')), self.formats['data_cell'])
                    worksheet.write(row, 7, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                    worksheet.write(row, 8, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                    worksheet.write(row, 9, quote.get('impact_score', 0), self.formats['number'])
                    
                    # Quote Classification dropdown
                    worksheet.data_validation(row, 10, row, 10, {
                        'validate': 'list',
                        'source': ['FEATURED - Key implementation insight', 'PRIMARY - Main implementation evidence', 'SUPPORTING - Background implementation context', 'EXCLUDE - Do not use']
                    })
                    worksheet.write(row, 10, "", self.formats['decision_cell'])
                    
                    # Theme Decision (only for first quote of each theme)
                    if first_quote or row == 6:  # First quote of first theme
                        worksheet.data_validation(row, 11, row, 11, {
                            'validate': 'list',
                            'source': ['VALIDATED - Use in report', 'REJECTED - Insufficient evidence', 'REVISED - Needs statement changes', 'MERGE - Combine with other theme']
                        })
                        worksheet.write(row, 11, "", self.formats['decision_cell'])
                    else:
                        worksheet.write(row, 11, "", self.formats['data_cell'])
                    
                    # Analyst Notes
                    worksheet.write(row, 12, "", self.formats['notes_cell'])
                    
                    # Theme Origin column (first quote row only)
                    worksheet.write(row, 13, theme.get('theme_origin', 'discovered').title(), self.formats['data_cell'])
                    
                    row += 1
                
                # Individual quote data (shifted by +1 from previous layout)
                worksheet.write(row, 0, "", self.formats['data_cell'])
                worksheet.write(row, 1, "", self.formats['data_cell'])
                worksheet.write(row, 2, "", self.formats['data_cell'])
                worksheet.write(row, 3, "", self.formats['data_cell'])
                worksheet.write(row, 4, "", self.formats['data_cell'])
                worksheet.write(row, 5, "", self.formats['data_cell'])
                worksheet.write(row, 6, "", self.formats['data_cell'])
                worksheet.write(row, 7, "", self.formats['data_cell'])
                worksheet.write(row, 8, "", self.formats['data_cell'])
                worksheet.write(row, 9, "", self.formats['data_cell'])
                worksheet.write(row, 10, "", self.formats['data_cell'])
                worksheet.write(row, 11, "", self.formats['data_cell'])
                worksheet.write(row, 12, "", self.formats['data_cell'])
                worksheet.write(row, 13, "", self.formats['data_cell'])
                worksheet.write(row, 14, "", self.formats['data_cell'])
                
                row += 1
            
            # Add Theme Decision Row after all quotes for this theme
            worksheet.write(row, 0, f"THEME DECISION: {theme['theme_id']}", self.formats['header'])
            worksheet.write(row, 1, "After reviewing all quotes above, make theme decision:", self.formats['subheader'])
            
            # Theme Decision dropdown
            worksheet.data_validation(row, 13, row, 13, {
                'validate': 'list',
                'source': ['PENDING REVIEW', 'VALIDATED - Include in Report', 'REJECTED - Exclude from Report', 'NEEDS REVISION', 'FEATURED - Highlight in Executive Summary']
            })
            worksheet.write(row, 13, "PENDING REVIEW", self.formats['pending'])
            
            # Theme-level analyst notes
            worksheet.write(row, 14, "", self.formats['notes_cell'])
            
            row += 1
            
            # Add a blank row between themes for visual separation
            row += 1
        
        # Add section summary
        row += 2
        worksheet.write(row, 0, "IMPLEMENTATION INSIGHTS SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Implementation Themes: {len(implementation_themes)}")
        worksheet.write(row, 3, "Validated Themes: [Count after review]")
        worksheet.write(row, 6, "Featured Quotes: [Count]")

    def _filter_themes_by_section(self, themes: List[Dict[str, Any]], section_type: str) -> List[Dict[str, Any]]:
        """Filter themes by report section type"""
        filtered_themes = []
        
        for theme in themes:
            theme_type = theme.get('theme_type', '').lower()
            subject = theme.get('harmonized_subject', '').lower()
            theme_statement = theme.get('theme_statement', '').lower()
            all_quotes = theme.get('all_quotes', [])
            
            if section_type == 'win':
                # Win drivers: strength themes, positive sentiment, high impact
                is_strength = theme_type == 'strength'
                is_positive_subject = subject in ['product capabilities', 'user experience', 'sales experience']
                has_positive_quotes = any(q.get('sentiment', '').lower() in ['positive', 'mixed'] for q in all_quotes)
                
                if is_strength or (is_positive_subject and has_positive_quotes):
                    filtered_themes.append(theme)
                    
            elif section_type == 'loss':
                # Loss factors: weakness themes, negative sentiment, competitive gaps
                is_weakness = theme_type == 'weakness'
                is_negative_subject = subject in ['pricing and commercial', 'competitive dynamics']
                has_negative_quotes = any(q.get('sentiment', '').lower() in ['negative', 'mixed'] for q in all_quotes)
                
                if is_weakness or (is_negative_subject and has_negative_quotes):
                    filtered_themes.append(theme)
                    
            elif section_type == 'competitive':
                # Competitive intelligence: competitive themes, market dynamics, any theme with competitor mentions
                is_competitive_subject = subject in ['competitive dynamics', 'market discovery']
                has_competitive_keyword = any(word in theme_statement for word in ['competitive', 'competitor', 'competition', 'versus', 'compared', 'alternative'])
                
                # Also check quotes for competitive content
                has_competitive_quotes = False
                for quote in all_quotes:
                    quote_text = quote.get('verbatim_response', '').lower()
                    if any(word in quote_text for word in ['competitor', 'competition', 'versus', 'compared', 'alternative', 'eve', 'evenup', 'parrot', 'filevine']):
                        has_competitive_quotes = True
                        break
                
                if is_competitive_subject or has_competitive_keyword or has_competitive_quotes:
                    filtered_themes.append(theme)
                    
            elif section_type == 'implementation':
                # Implementation insights: implementation, integration, technical themes
                is_implementation_subject = subject in ['implementation process', 'integration technical', 'support and service']
                has_implementation_keyword = any(word in theme_statement for word in ['implementation', 'integration', 'setup', 'onboarding', 'deployment', 'technical'])
                
                # Also check quotes for implementation content
                has_implementation_quotes = False
                for quote in all_quotes:
                    quote_text = quote.get('verbatim_response', '').lower()
                    if any(word in quote_text for word in ['implementation', 'integration', 'setup', 'onboarding', 'deployment', 'technical', 'process']):
                        has_implementation_quotes = True
                        break
                
                if is_implementation_subject or has_implementation_keyword or has_implementation_quotes:
                    filtered_themes.append(theme)
        
        return filtered_themes

    def _map_theme_to_research_question(self, theme: Dict[str, Any]) -> str:
        """Map theme to specific research question using DB-backed evidence when available.
        Prefers the primary question inferred from the quotes (which now uses the DB question per quote).
        """
        # Prefer research alignment primary question (derived from quotes' primary_research_question)
        research_alignment = theme.get('research_alignment', {})
        if research_alignment and research_alignment.get('primary_question'):
            return research_alignment['primary_question']

        # As a fallback, try to read a DB-sourced question on the theme if present
        if theme.get('primary_research_question'):
            return theme['primary_research_question']

        # Fallback to discussion guide if no alignment data
        discussion_guide = getattr(self, 'discussion_guide', None)
        if discussion_guide and len(discussion_guide) > 0:
            questions = discussion_guide
            subject = theme.get('harmonized_subject', '').lower()
            theme_statement = theme.get('theme_statement', '').lower()
            for question in questions:
                question_lower = question.lower()
                if any(word in subject or word in theme_statement for word in question_lower.split()[:5]):
                    return question
            return questions[0] if questions else "Research question not specified"

        # Final fallback to hardcoded questions
        subject = theme.get('harmonized_subject', '').lower()
        if 'product' in subject or 'capabilities' in subject:
            return "What product features drive vendor selection decisions?"
        elif 'pricing' in subject or 'commercial' in subject:
            return "How do pricing models influence purchase decisions?"
        elif 'implementation' in subject:
            return "What implementation challenges affect vendor satisfaction?"
        elif 'sales' in subject:
            return "How does the sales process impact vendor perception?"
        elif 'competitive' in subject:
            return "How do vendors compare in the competitive landscape?"
        elif 'user' in subject or 'experience' in subject:
            return "What usability factors influence user adoption?"
        elif 'market' in subject:
            return "What market needs are driving vendor evaluation?"
        elif 'support' in subject or 'service' in subject:
            return "How does ongoing support affect vendor relationships?"
        elif 'integration' in subject or 'technical' in subject:
            return "What technical requirements drive integration decisions?"
        else:
            return "Research question not specified"

    def _create_evidence_validation_tab(self, themes_data: Dict[str, Any]):
        """Phase 2: Evidence-First Theme Validation - Show theme with ALL evidence for validation"""
        worksheet = self.workbook.add_worksheet('Phase 2 - Theme Validation')
        
        # Set column widths for evidence validation
        worksheet.set_column('A:A', 12)  # Theme ID
        worksheet.set_column('B:B', 50)  # Auto-Generated Theme Statement
        worksheet.set_column('C:C', 80)  # ALL Supporting Evidence
        worksheet.set_column('D:D', 20)  # Evidence Strength
        worksheet.set_column('E:E', 20)  # Statement Accuracy
        worksheet.set_column('F:F', 50)  # Analyst-Revised Statement
        worksheet.set_column('G:G', 20)  # Theme Status
        worksheet.set_column('H:H', 30)  # Research Connection
        worksheet.set_column('I:I', 40)  # Validation Notes
        worksheet.set_column('J:J', 40)  # Verbatim Question (DB)
        
        # Title and instructions
        worksheet.merge_range('A1:J1', "Phase 2: Evidence-First Theme Validation", self.formats['title'])
        worksheet.merge_range('A2:J2', "PURPOSE: For each discovered theme, review ALL evidence to determine if it's real and accurately stated. Only validated themes advance to quote curation.", self.formats['subheader'])
        
        # Headers
        headers = [
            "Theme ID", "Auto-Generated Theme Statement", "ALL Supporting Evidence", "Evidence Strength",
            "Statement Accuracy", "Analyst-Revised Statement", "Theme Status", "Research Connection", "Validation Notes", "Verbatim Question (DB)"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Process each theme for validation
        row = 4
        for theme in themes_data['themes']:
            all_quotes = theme.get('all_quotes', [])
            
            # Theme ID
            worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
            
            # Auto-Generated Theme Statement
            theme_statement = theme.get('theme_statement', 'No statement generated')
            worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
            
            # ALL Supporting Evidence - comprehensive view
            evidence_text = self._create_comprehensive_evidence_view(theme, all_quotes)
            worksheet.write(row, 2, evidence_text, self.formats['data_cell'])
            
            # Evidence Strength Assessment
            worksheet.data_validation(row, 3, row, 3, {
                'validate': 'list',
                'source': ['SUFFICIENT - Strong evidence', 'MODERATE - Some gaps', 'INSUFFICIENT - Weak evidence', 'CONTRADICTORY - Mixed signals']
            })
            worksheet.write(row, 3, "", self.formats['decision_cell'])
            
            # Statement Accuracy Assessment
            worksheet.data_validation(row, 4, row, 4, {
                'validate': 'list',
                'source': ['ACCURATE - Reflects evidence', 'NEEDS REVISION - Close but off', 'INACCURATE - Does not match', 'TOO BROAD - Overstated', 'TOO NARROW - Understated']
            })
            worksheet.write(row, 4, "", self.formats['decision_cell'])
            
            # Analyst-Revised Statement
            worksheet.write(row, 5, "", self.formats['notes_cell'])
            
            # Theme Status (Final Decision)
            worksheet.data_validation(row, 6, row, 6, {
                'validate': 'list',
                'source': ['VALIDATED - Advance to curation', 'REJECTED - Insufficient evidence', 'MERGED - Combine with other theme', 'PENDING - Needs more review']
            })
            worksheet.write(row, 6, "", self.formats['decision_cell'])
            
            # Research Connection
            research_connection = self._map_theme_to_research_area(theme)
            worksheet.write(row, 7, research_connection, self.formats['data_cell'])
            
            # Validation Notes
            worksheet.write(row, 8, "", self.formats['notes_cell'])
            
            # DB Question for quick reference
            # Use the first non-empty question among this theme's quotes
            db_q = next((q.get('question') for q in all_quotes if q.get('question')), '')
            worksheet.write(row, 9, db_q, self.formats['data_cell'])
            
            row += 1
        
        # Add validation summary
        row += 2
        worksheet.write(row, 0, "VALIDATION SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Themes for Validation: {len(themes_data['themes'])}")
        worksheet.write(row, 3, "Validated Themes: [Count after review]")
        worksheet.write(row, 6, "Validation Complete: [Yes/No]")

    def _create_comprehensive_evidence_view(self, theme: Dict[str, Any], all_quotes: List[Dict]) -> str:
        """Create comprehensive evidence view for validation (more detailed than previous)"""
        if not all_quotes:
            return "❌ NO EVIDENCE FOUND - This theme has no supporting quotes"
        
        evidence_parts = []
        
        # Theme context
        evidence_parts.append(f"🎯 THEME: {theme.get('theme_statement', 'No statement')}")
        evidence_parts.append(f"📊 EVIDENCE SCOPE: {len(all_quotes)} quotes across {len(set(q.get('company', q.get('company_name', 'Unknown')) for q in all_quotes))} companies")
        evidence_parts.append("=" * 60)
        
        # Group by company and show ALL quotes (not just top 3)
        quotes_by_company = {}
        for quote in all_quotes:
            company = quote.get('company', quote.get('company_name', 'Unknown'))
            if company not in quotes_by_company:
                quotes_by_company[company] = []
            quotes_by_company[company].append(quote)
        
        # Show comprehensive evidence by company
        for company, company_quotes in quotes_by_company.items():
            evidence_parts.append(f"\n🏢 {company.upper()} ({len(company_quotes)} quotes):")
            
            for i, quote in enumerate(company_quotes, 1):
                sentiment = quote.get('sentiment', 'unknown').upper()
                impact = quote.get('impact_score', 0)
                interviewee = quote.get('interviewee_name', 'Unknown')
                
                # Full quote text for validation (not truncated)
                quote_text = quote.get('verbatim_response', 'No quote text')
                
                evidence_parts.append(f"\n  {i}. [{sentiment}, Impact: {impact}] {interviewee}:")
                evidence_parts.append(f"     \"{quote_text}\"")
        
        # Evidence quality indicators
        evidence_parts.append(f"\n📈 EVIDENCE ANALYSIS:")
        sentiments = [q.get('sentiment', 'unknown') for q in all_quotes]
        avg_impact = sum(q.get('impact_score', 0) for q in all_quotes) / len(all_quotes) if all_quotes else 0
        
        evidence_parts.append(f"• Average Impact Score: {avg_impact:.1f}/5")
        evidence_parts.append(f"• Sentiment Distribution: {dict(zip(*zip(*[(s, sentiments.count(s)) for s in set(sentiments)])))}") 
        evidence_parts.append(f"• Cross-Company Validation: {len(quotes_by_company)} companies represented")
        evidence_parts.append(f"• Evidence Depth: {len(all_quotes)} total quotes")
        
        return "\n".join(evidence_parts)

    def _map_theme_to_research_area(self, theme: Dict[str, Any]) -> str:
        """Map theme to likely research question area"""
        subject = theme.get('harmonized_subject', '').lower()
        theme_type = theme.get('theme_type', '').lower()
        
        # Simple mapping based on subject and theme type
        if 'product' in subject or 'capabilities' in subject:
            return "Product feature evaluation"
        elif 'pricing' in subject or 'commercial' in subject:
            return "Pricing model assessment"
        elif 'implementation' in subject:
            return "Implementation challenges"
        elif 'sales' in subject:
            return "Sales process evaluation"
        elif 'competitive' in subject:
            return "Competitive positioning"
        elif 'user' in subject or 'experience' in subject:
            return "User experience factors"
        else:
            return "General market insights"

    def _create_quote_curation_tab(self, themes_data: Dict[str, Any]):
        """Phase 3: Quote-by-Quote Curation for validated themes only"""
        worksheet = self.workbook.add_worksheet('Phase 3 - Quote Curation')
        
        # Set column widths
        worksheet.set_column('A:A', 12)  # Theme ID
        worksheet.set_column('B:B', 40)  # Validated Theme Statement
        worksheet.set_column('C:C', 50)  # Individual Quote
        worksheet.set_column('D:D', 15)  # Company
        worksheet.set_column('E:E', 15)  # Interviewee
        worksheet.set_column('F:F', 12)  # Impact Score
        worksheet.set_column('G:G', 12)  # Sentiment
        worksheet.set_column('H:H', 20)  # Evidence Quality
        worksheet.set_column('I:I', 18)  # Usage Level
        worksheet.set_column('J:J', 25)  # Research Question
        worksheet.set_column('K:K', 30)  # Quote Notes
        
        # Title and instructions
        worksheet.merge_range('A1:K1', "Phase 3: Quote-by-Quote Evidence Curation", self.formats['title'])
        worksheet.merge_range('A2:K2', "PURPOSE: For validated themes only, curate individual quotes by evidence strength and usage level. Build evidence hierarchy for report writing.", self.formats['subheader'])
        
        # Headers
        headers = [
            "Theme ID", "Validated Theme Statement", "Individual Quote", "Company", "Interviewee",
            "Impact Score", "Sentiment", "Evidence Quality", "Usage Level", "Research Question", "Quote Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Instructions for analyst
        row = 4
        worksheet.write(row, 0, "INSTRUCTIONS:", self.formats['header'])
        worksheet.write(row, 1, "1. Only themes marked 'VALIDATED' in Phase 2 should appear here", self.formats['data_cell'])
        row += 1
        worksheet.write(row, 1, "2. Rate each quote's evidence quality for the specific theme", self.formats['data_cell'])
        row += 1
        worksheet.write(row, 1, "3. Assign usage level based on quote strength and relevance", self.formats['data_cell'])
        row += 1
        worksheet.write(row, 1, "4. Featured quotes should be your strongest evidence for executive summary", self.formats['data_cell'])
        row += 2
        
        # Create quote curation rows for each theme
        # Note: In real implementation, this would only show validated themes
        for theme in themes_data['themes']:
            all_quotes = theme.get('all_quotes', [])
            
            for quote in all_quotes:
                # Theme ID
                worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
                
                # Validated Theme Statement (placeholder - would come from Phase 2)
                theme_statement = f"[VALIDATED VERSION FROM PHASE 2: {theme.get('theme_statement', '')[:50]}...]"
                worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
                
                # Individual Quote
                quote_text = quote.get('verbatim_response', 'No quote')
                worksheet.write(row, 2, quote_text, self.formats['data_cell'])
                
                # Company & Interviewee
                company = quote.get('company', quote.get('company_name', 'Unknown'))
                worksheet.write(row, 3, company, self.formats['data_cell'])
                worksheet.write(row, 4, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                
                # Impact Score & Sentiment
                worksheet.write(row, 5, quote.get('impact_score', 0), self.formats['number'])
                worksheet.write(row, 6, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                
                # Evidence Quality Assessment
                worksheet.data_validation(row, 7, row, 7, {
                    'validate': 'list',
                    'source': ['STRONG PROOF - Perfect example', 'SUPPORTING - Good evidence', 'WEAK - Tangential', 'IRRELEVANT - Does not support']
                })
                worksheet.write(row, 7, "", self.formats['decision_cell'])
                
                # Usage Level Assignment  
                worksheet.data_validation(row, 8, row, 8, {
                    'validate': 'list',
                    'source': ['FEATURED - Executive summary', 'PRIMARY - Main evidence', 'SUPPORTING - Background', 'EXCLUDE - Do not use']
                })
                worksheet.write(row, 8, "", self.formats['decision_cell'])
                
                # Research Question Connection
                research_connection = self._map_theme_to_research_area(theme)
                worksheet.write(row, 9, research_connection, self.formats['data_cell'])
                
                # Quote Notes
                worksheet.write(row, 10, "", self.formats['notes_cell'])
                
                row += 1
                
                # Limit quotes per theme for readability
                if row > 50:  # Practical limit for Excel usability
                    break
            
            if row > 50:
                break
        
        # Add curation summary
        row += 2
        worksheet.write(row, 0, "CURATION SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, "Featured Quotes: [Count]")
        worksheet.write(row, 3, "Primary Evidence: [Count]") 
        worksheet.write(row, 6, "Supporting Quotes: [Count]")
        worksheet.write(row, 9, "Total Curated: [Count]")

    def _create_integrated_review_tab(self, themes_data: Dict[str, Any]):
        """Create integrated theme-evidence review tab where analysts see themes with all supporting quotes"""
        worksheet = self.workbook.add_worksheet('🔍 Theme-Evidence Review')
        
        # Set column widths for integrated view
        worksheet.set_column('A:A', 12)  # Theme ID
        worksheet.set_column('B:B', 45)  # Theme Title
        worksheet.set_column('C:C', 18)  # Win-Loss Category  
        worksheet.set_column('D:D', 18)  # Report Section
        worksheet.set_column('E:E', 12)  # Quality Score
        worksheet.set_column('F:F', 18)  # Theme Rating
        worksheet.set_column('G:G', 80)  # Supporting Evidence (All Quotes)
        worksheet.set_column('H:H', 25)  # Evidence Strength
        worksheet.set_column('I:I', 15)  # Company Coverage
        worksheet.set_column('J:J', 40)  # Analyst Notes
        worksheet.set_column('K:K', 15)  # Priority
        
        # Title and instructions
        worksheet.merge_range('A1:K1', "Integrated Theme-Evidence Review - Make Decisions with Full Context", self.formats['title'])
        worksheet.merge_range('A2:K2', "WORKFLOW: For each theme, review ALL supporting quotes (Column G) → Assess evidence strength (Column H) → Set theme rating (Column F) → Assign to report section (Column D)", self.formats['subheader'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Title", "Win-Loss Category", "Report Section", "Quality Score",
            "Theme Rating", "Supporting Evidence (All Quotes)", "Evidence Strength", 
            "Company Coverage", "Analyst Notes", "Priority"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Process each theme with all its evidence
        row = 4
        for theme in themes_data['themes']:
            # Get all quotes for this theme
            all_quotes = theme.get('all_quotes', [])
            supporting_quotes = theme.get('supporting_quotes', [])
            
            # Theme basic info
            worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
            
            theme_title = theme.get('theme_title', f"Theme {theme['theme_id']}")
            worksheet.write(row, 1, theme_title, self.formats['data_cell'])
            
            # Win-Loss Category with dropdown
            win_loss_category = self._determine_win_loss_category(theme)
            worksheet.data_validation(row, 2, row, 2, {
                'validate': 'list',
                'source': ['Strength', 'Weakness', 'Opportunity', 'Competitive', 'Process']
            })
            worksheet.write(row, 2, win_loss_category, self.formats['data_cell'])
            
            # Report Section with dropdown
            report_section = self._determine_report_section(win_loss_category)
            worksheet.data_validation(row, 3, row, 3, {
                'validate': 'list',
                'source': ['Section 2: Why You Win', 'Section 3: Why You Lose', 'Section 4: Market Opportunities', 'Section 5: Competitive Intelligence', 'Section 6: Implementation Insights']
            })
            worksheet.write(row, 3, report_section, self.formats['data_cell'])
            
            # Quality Score
            worksheet.write(row, 4, theme['validation_metrics']['quality_score'], self.formats['number'])
            
            # Theme Rating dropdown (Featured/Include/Exclude)
            worksheet.data_validation(row, 5, row, 5, {
                'validate': 'list',
                'source': ['FEATURED', 'INCLUDE', 'EXCLUDE']
            })
            worksheet.write(row, 5, "", self.formats['decision_cell'])
            
            # Supporting Evidence - ALL quotes with context
            evidence_text = self._create_integrated_evidence_view(theme, all_quotes, supporting_quotes)
            worksheet.write(row, 6, evidence_text, self.formats['data_cell'])
            
            # Evidence Strength Assessment dropdown
            worksheet.data_validation(row, 7, row, 7, {
                'validate': 'list',
                'source': ['STRONG - Multiple companies, clear pattern', 'MODERATE - Some validation needed', 'WEAK - Limited evidence', 'INSUFFICIENT - Needs more quotes']
            })
            worksheet.write(row, 7, "", self.formats['decision_cell'])
            
            # Company Coverage
            company_dist = theme['validation_metrics'].get('company_distribution', {})
            dist_summary = company_dist.get('distribution_summary', f"{theme['validation_metrics']['companies_count']} companies")
            worksheet.write(row, 8, dist_summary, self.formats['data_cell'])
            
            # Analyst Notes
            worksheet.write(row, 9, "", self.formats['notes_cell'])
            
            # Priority dropdown
            worksheet.data_validation(row, 10, row, 10, {
                'validate': 'list',
                'source': ['HIGH', 'MEDIUM', 'LOW']
            })
            worksheet.write(row, 10, "", self.formats['decision_cell'])
            
            row += 1
        
        # Add summary section
        row += 2
        worksheet.write(row, 0, "INTEGRATION SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Themes for Review: {len(themes_data['themes'])}")
        worksheet.write(row, 3, f"Total Supporting Quotes: {sum(len(theme.get('all_quotes', [])) for theme in themes_data['themes'])}")
        worksheet.write(row, 6, "Complete evidence review before making theme decisions")

    def _create_integrated_evidence_view(self, theme: Dict[str, Any], all_quotes: List[Dict], supporting_quotes: List[Dict]) -> str:
        """Create integrated view of all evidence for a theme"""
        if not all_quotes:
            return "No quotes available"
        
        evidence_parts = []
        
        # Add theme statement for context
        evidence_parts.append(f"THEME: {theme.get('theme_statement', 'No statement')}")
        evidence_parts.append("=" * 50)
        
        # Group quotes by company for better organization
        quotes_by_company = {}
        for quote in all_quotes:
            company = quote.get('company', quote.get('company_name', 'Unknown'))
            if company not in quotes_by_company:
                quotes_by_company[company] = []
            quotes_by_company[company].append(quote)
        
        # Display quotes organized by company
        for company, company_quotes in quotes_by_company.items():
            evidence_parts.append(f"\n📍 {company} ({len(company_quotes)} quotes):")
            
            for i, quote in enumerate(company_quotes[:3], 1):  # Limit to top 3 per company
                sentiment = quote.get('sentiment', 'unknown').upper()
                impact = quote.get('impact_score', 0)
                interviewee = quote.get('interviewee_name', 'Unknown')
                
                # Mark if this is a supporting quote
                is_supporting = any(sq.get('response_id') == quote.get('response_id') for sq in supporting_quotes)
                support_marker = "⭐ " if is_supporting else "• "
                
                quote_text = quote.get('verbatim_response', '')[:200] + "..." if len(quote.get('verbatim_response', '')) > 200 else quote.get('verbatim_response', '')
                
                evidence_parts.append(f"  {support_marker}[{sentiment}, Impact: {impact}] {interviewee}: \"{quote_text}\"")
            
            if len(company_quotes) > 3:
                evidence_parts.append(f"  ... and {len(company_quotes) - 3} more quotes from {company}")
        
        # Add summary stats
        evidence_parts.append(f"\n📊 EVIDENCE SUMMARY:")
        evidence_parts.append(f"• Total Quotes: {len(all_quotes)} across {len(quotes_by_company)} companies")
        evidence_parts.append(f"• Top Supporting: {len(supporting_quotes)} quotes (marked with ⭐)")
        evidence_parts.append(f"• Avg Impact: {sum(q.get('impact_score', 0) for q in all_quotes) / len(all_quotes):.1f}")
        
        return "\n".join(evidence_parts)
    
    def _create_theme_curation_tab(self, themes_data: Dict[str, Any]):
        """Create the main theme curation workspace"""
        worksheet = self.workbook.add_worksheet('🎯 Theme Curation')
        
        # Set column widths
        worksheet.set_column('A:A', 12)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Title
        worksheet.set_column('C:C', 60)  # Theme Statement  
        worksheet.set_column('D:D', 15)  # Theme Type
        worksheet.set_column('E:E', 20)  # Subject
        worksheet.set_column('F:F', 18)  # Win-Loss Category
        worksheet.set_column('G:G', 18)  # Report Section
        worksheet.set_column('H:H', 12)  # Quality Score
        worksheet.set_column('I:I', 20)  # Company Distribution
        worksheet.set_column('J:J', 50)  # Evidence Preview
        worksheet.set_column('K:K', 15)  # Quality Flags
        worksheet.set_column('L:L', 18)  # Theme Rating (Featured/Include/Exclude)
        worksheet.set_column('M:M', 40)  # Analyst Notes
        worksheet.set_column('N:N', 15)  # Priority Level

        # Title
        worksheet.merge_range('A1:N1', "Theme Curation & Section Assignment Workspace", self.formats['title'])

        # Instructions
        worksheet.merge_range('A2:N2', "INSTRUCTIONS: 1) Review evidence preview (Column J) 2) Assign win-loss category (Column F) 3) Set theme rating (Column L) 4) Assign to report section (Column G). This organizes themes for structured win-loss reporting.", self.formats['subheader'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Title", "Theme Statement", "Type", "Subject Category",
            "Win-Loss Category", "Report Section", "Quality Score", "Company Distribution", 
            "Evidence Preview", "Quality Flags", "Theme Rating", "Analyst Notes", "Priority Level"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Theme data
        row = 4
        for theme in themes_data['themes']:
            # Theme ID
            worksheet.write(row, 0, theme['theme_id'])
            
            # Theme Title (new column)
            theme_title = theme.get('theme_title', f"Theme {theme['theme_id']}")
            worksheet.write(row, 1, theme_title, self.formats['data_cell'])
            
            # Theme Statement
            worksheet.write(row, 2, theme['theme_statement'], self.formats['data_cell'])
            
            # Theme Type with formatting
            theme_type = theme['theme_type']
            theme_format = self.formats.get(theme_type, self.formats['data_cell'])
            worksheet.write(row, 3, theme_type.replace('_', ' ').title(), theme_format)
            
            # Subject Category
            worksheet.write(row, 4, theme['harmonized_subject'])
            
            # Win-Loss Category (new column)
            win_loss_category = self._determine_win_loss_category(theme)
            worksheet.data_validation(row, 5, row, 5, {
                'validate': 'list',
                'source': ['Strength', 'Weakness', 'Opportunity', 'Competitive', 'Process']
            })
            worksheet.write(row, 5, win_loss_category, self.formats['data_cell'])
            
            # Report Section (new column) 
            report_section = self._determine_report_section(win_loss_category)
            worksheet.data_validation(row, 6, row, 6, {
                'validate': 'list',
                'source': ['Section 2: Why You Win', 'Section 3: Why You Lose', 'Section 4: Market Opportunities', 'Section 5: Competitive Intelligence', 'Section 6: Implementation Insights']
            })
            worksheet.write(row, 6, report_section, self.formats['data_cell'])
            
            # Quality Score
            worksheet.write(row, 7, theme['validation_metrics']['quality_score'], self.formats['number'])
            
            # Company Distribution
            company_dist = theme['validation_metrics'].get('company_distribution', {})
            dist_summary = company_dist.get('distribution_summary', f"{theme['validation_metrics']['companies_count']} companies")
            worksheet.write(row, 8, dist_summary, self.formats['data_cell'])
            
            # Evidence Preview (Top 2 supporting quotes)
            evidence_preview = self._create_evidence_preview(theme)
            worksheet.write(row, 9, evidence_preview, self.formats['data_cell'])
            
            # Quality Flags
            quality_flags = self._assign_quality_flags(theme)
            worksheet.write(row, 10, ", ".join(quality_flags), self.formats['data_cell'])
            
            # Theme Rating Cell (dropdown) - Featured/Include/Exclude
            worksheet.data_validation(row, 11, row, 11, {
                'validate': 'list',
                'source': ['FEATURED', 'INCLUDE', 'EXCLUDE']
            })
            worksheet.write(row, 11, "", self.formats['decision_cell'])
            
            # Notes Cell
            worksheet.write(row, 12, "", self.formats['notes_cell'])
            
            # Priority Cell (dropdown)
            worksheet.data_validation(row, 13, row, 13, {
                'validate': 'list', 
                'source': ['HIGH', 'MEDIUM', 'LOW']
            })
            worksheet.write(row, 13, "", self.formats['decision_cell'])
            
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
        worksheet.set_column('D:D', 40)  # Theme Title
        worksheet.set_column('E:E', 18)  # Report Section
        worksheet.set_column('F:F', 50)  # Full Theme Statement
        worksheet.set_column('G:G', 50)  # Verbatim Quote
        worksheet.set_column('H:H', 12)  # Sentiment
        worksheet.set_column('I:I', 12)  # Impact Score
        worksheet.set_column('J:J', 15)  # Company
        worksheet.set_column('K:K', 15)  # Interviewee
        worksheet.set_column('L:L', 18)  # Quote Rating
        worksheet.set_column('M:M', 30)  # Quote Notes
        
        # Title
        worksheet.merge_range('A1:M1', "Quote Analysis & Selection for Final Report", self.formats['title'])
        
        # Headers
        headers = [
            "Response ID", "Original Question", "Theme ID", "Theme Title", "Report Section", "Full Theme Statement",
            "Verbatim Quote", "Sentiment", "Impact Score", "Company", "Interviewee", 
            "Quote Rating", "Quote Notes"
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
                
                # Theme Title
                theme_title = theme.get('theme_title', f"Theme {theme['theme_id']}")
                worksheet.write(row, 3, theme_title, self.formats['data_cell'])
                
                # Report Section
                win_loss_category = self._determine_win_loss_category(theme)
                report_section = self._determine_report_section(win_loss_category)
                worksheet.write(row, 4, report_section, self.formats['data_cell'])
                
                # Full Theme Statement
                worksheet.write(row, 5, theme['theme_statement'], self.formats['data_cell'])
                
                # Verbatim Quote
                worksheet.write(row, 6, quote['verbatim_response'], self.formats['data_cell'])
                
                # Sentiment
                sentiment = quote.get('sentiment', 'unknown').title()
                worksheet.write(row, 7, sentiment)
                
                # Impact Score
                worksheet.write(row, 8, quote.get('impact_score', 0), self.formats['number'])
                
                # Company (handle both column names)
                company = quote.get('company', quote.get('company_name', 'Unknown'))
                worksheet.write(row, 9, company)
                
                # Interviewee
                worksheet.write(row, 10, quote.get('interviewee_name', ''))
                
                # Quote Rating dropdown (Featured/Include/Exclude)
                worksheet.data_validation(row, 11, row, 11, {
                    'validate': 'list',
                    'source': ['FEATURED', 'INCLUDE', 'EXCLUDE']
                })
                worksheet.write(row, 11, "", self.formats['decision_cell'])
                
                # Quote Notes
                worksheet.write(row, 12, "", self.formats['notes_cell'])
                
                row += 1

    def _create_section_planning_tab(self, themes_data: Dict[str, Any]):
        """Create section planning dashboard for report structure"""
        worksheet = self.workbook.add_worksheet('Section Planning')
        
        # Set column widths
        worksheet.set_column('A:A', 25)  # Section Name
        worksheet.set_column('B:B', 15)  # Featured Count
        worksheet.set_column('C:C', 15)  # Include Count
        worksheet.set_column('D:D', 15)  # Total Themes
        worksheet.set_column('E:E', 20)  # Question Coverage
        worksheet.set_column('F:F', 60)  # Key Themes Preview
        worksheet.set_column('G:G', 20)  # Strength Assessment
        
        # Title
        worksheet.merge_range('A1:G1', "Win-Loss Report Section Planning Dashboard", self.formats['title'])
        
        # Instructions
        worksheet.merge_range('A2:G2', "OVERVIEW: This dashboard shows how themes will be distributed across report sections. Use this to ensure balanced coverage and strong narratives for each section.", self.formats['subheader'])
        
        # Section summary
        section_summary = self._analyze_section_distribution(themes_data['themes'])
        
        # Headers
        headers = [
            "Report Section", "Featured Themes", "Include Themes", "Total Themes",
            "Question Coverage", "Key Themes Preview", "Strength Assessment"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Section data
        row = 4
        sections = [
            "Section 2: Why You Win",
            "Section 3: Why You Lose", 
            "Section 4: Market Opportunities",
            "Section 5: Competitive Intelligence",
            "Section 6: Implementation Insights"
        ]
        
        for section in sections:
            section_data = section_summary.get(section, {})
            
            # Section Name
            worksheet.write(row, 0, section, self.formats['data_cell'])
            
            # Featured Count
            featured_count = section_data.get('featured_count', 0)
            worksheet.write(row, 1, featured_count, self.formats['number'])
            
            # Include Count  
            include_count = section_data.get('include_count', 0)
            worksheet.write(row, 2, include_count, self.formats['number'])
            
            # Total Themes
            total_count = featured_count + include_count
            worksheet.write(row, 3, total_count, self.formats['number'])
            
            # Question Coverage (placeholder)
            worksheet.write(row, 4, "To Be Determined", self.formats['data_cell'])
            
            # Key Themes Preview
            key_themes = section_data.get('key_themes', [])
            themes_preview = "; ".join(key_themes[:2]) if key_themes else "No themes assigned"
            worksheet.write(row, 5, themes_preview, self.formats['data_cell'])
            
            # Strength Assessment
            strength = self._assess_section_strength(featured_count, include_count, total_count)
            worksheet.write(row, 6, strength, self.formats['data_cell'])
            
            row += 1
        
        # Add summary statistics
        row += 2
        worksheet.write(row, 0, "REPORT SUMMARY:", self.formats['header'])
        row += 1
        
        total_featured = sum(section_summary.get(s, {}).get('featured_count', 0) for s in sections)
        total_include = sum(section_summary.get(s, {}).get('include_count', 0) for s in sections)
        
        worksheet.write(row, 0, f"Total Featured Themes: {total_featured}")
        worksheet.write(row, 3, f"Total Include Themes: {total_include}")
        worksheet.write(row, 6, f"Grand Total: {total_featured + total_include}")

    def _analyze_section_distribution(self, themes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how themes are distributed across report sections"""
        section_analysis = {}
        
        for theme in themes:
            # Determine section for this theme
            win_loss_category = self._determine_win_loss_category(theme)
            report_section = self._determine_report_section(win_loss_category)
            
            if report_section not in section_analysis:
                section_analysis[report_section] = {
                    'featured_count': 0,
                    'include_count': 0,
                    'key_themes': []
                }
            
            # For now, assume all themes are "Include" level
            # In reality, this would come from analyst decisions
            section_analysis[report_section]['include_count'] += 1
            
            # Add theme title to key themes
            theme_title = theme.get('theme_title', f"Theme {theme.get('theme_id', '')}")
            section_analysis[report_section]['key_themes'].append(theme_title)
        
        return section_analysis
    
    def _assess_section_strength(self, featured_count: int, include_count: int, total_count: int) -> str:
        """Assess the strength of evidence for a report section"""
        if featured_count >= 2:
            return "STRONG - Executive Ready"
        elif featured_count >= 1:
            return "GOOD - Solid Evidence" 
        elif include_count >= 3:
            return "MODERATE - Needs Curation"
        elif total_count >= 1:
            return "WEAK - Limited Evidence"
        else:
            return "MISSING - No Themes"

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
        worksheet.set_column('E:E', 50)  # Question (DB)
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
        
        # Initialize navigation maps
        self.raw_data_q_first_row = {}
        self.raw_data_q_companies = {}
        self.raw_data_q_quotes = {}
        
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
            
            # Record first row anchor and counts by question
            q_text = (quote.get('question', '') or '').strip()
            norm_q = q_text.lower()
            if q_text:
                if norm_q not in self.raw_data_q_first_row:
                    # Store 1-indexed Excel row number for hyperlinks
                    self.raw_data_q_first_row[norm_q] = row + 1
                # Count quotes
                self.raw_data_q_quotes[norm_q] = self.raw_data_q_quotes.get(norm_q, 0) + 1
                # Track unique companies
                if norm_q not in self.raw_data_q_companies:
                    self.raw_data_q_companies[norm_q] = set()
                self.raw_data_q_companies[norm_q].add(company)
            row += 1
    
    def _create_unified_report_builder_tab(self, themes_data: Dict[str, Any]):
        """Create unified report builder with decision tracking and outline generation"""
        worksheet = self.workbook.add_worksheet('Report Builder')
        
        # Set column widths
        worksheet.set_column('A:A', 20)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 15)  # Section
        worksheet.set_column('D:D', 15)  # Quality Score
        worksheet.set_column('E:E', 25)  # Decision
        worksheet.set_column('F:F', 40)  # Notes
        worksheet.set_column('G:G', 30)  # Report Impact
        
        # Title and instructions
        worksheet.merge_range('A1:G1', "📋 UNIFIED REPORT BUILDER", self.formats['title'])
        worksheet.merge_range('A2:G2', "Make decisions, see live updates, and generate report outline", self.formats['subheader'])
        
        row = 4
        
        # Instructions
        worksheet.write(row, 0, "📝 HOW TO USE:", self.formats['header'])
        worksheet.merge_range(f'A{row}:G{row}', "1. Review themes below 2. Mark decisions 3. See live report outline 4. Copy to design team", self.formats['data_cell'])
        row += 1
        
        # Headers
        headers = ["Theme ID", "Theme Statement", "Section", "Quality Score", "Decision", "Notes", "Report Impact"]
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1
        
        # Add all themes for decision tracking
        all_themes = themes_data['themes']
        for theme in all_themes:
            theme_id = theme.get('theme_id', 'unknown')
            theme_statement = theme.get('theme_statement', 'No statement')[:80] + "..." if len(theme.get('theme_statement', '')) > 80 else theme.get('theme_statement', '')
            section = self._determine_report_section(theme.get('win_loss_category', 'unknown'))
            quality_score = theme.get('validation_metrics', {}).get('quality_score', 0)
            
            worksheet.write(row, 0, theme_id, self.formats['data_cell'])
            worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
            worksheet.write(row, 2, section, self.formats['data_cell'])
            worksheet.write(row, 3, f"{quality_score:.1f}", self.formats['data_cell'])
            
            # Decision dropdown
            worksheet.data_validation(row, 4, row, 4, {
                'validate': 'list',
                'source': ['PENDING', 'VALIDATED', 'FEATURED', 'REJECTED', 'NEEDS REVISION']
            })
            worksheet.write(row, 4, "PENDING", self.formats['pending'])
            
            # Notes cell
            worksheet.write(row, 5, "", self.formats['notes_cell'])
            
            # Report Impact (formula-based)
            impact_formula = f'=IF(E{row+1}="VALIDATED","Include in Report",IF(E{row+1}="FEATURED","Executive Summary",IF(E{row+1}="REJECTED","Exclude",IF(E{row+1}="NEEDS REVISION","Revise First","Pending Review"))))'
            worksheet.write_formula(row, 6, impact_formula, self.formats['data_cell'])
            
            row += 1
        
        # Add summary section
        row += 2
        worksheet.write(row, 0, "📊 DECISION SUMMARY:", self.formats['header'])
        row += 1
        
        # Add formula-based counters
        worksheet.write(row, 0, "Total Themes:")
        total_formula = f'=COUNTA(A6:A{row-3})'
        worksheet.write_formula(row, 1, total_formula, self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Validated Themes:")
        validated_formula = f'=COUNTIF(E6:E{row-2},"VALIDATED")'
        worksheet.write_formula(row, 1, validated_formula, self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Featured Themes:")
        featured_formula = f'=COUNTIF(E6:E{row-2},"FEATURED")'
        worksheet.write_formula(row, 1, featured_formula, self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Rejected Themes:")
        rejected_formula = f'=COUNTIF(E6:E{row-2},"REJECTED")'
        worksheet.write_formula(row, 1, rejected_formula, self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Needs Revision:")
        revision_formula = f'=COUNTIF(E6:E{row-2},"NEEDS REVISION")'
        worksheet.write_formula(row, 1, revision_formula, self.formats['data_cell'])
        row += 2
        
        # Report Outline Section
        worksheet.write(row, 0, "📋 REPORT OUTLINE:", self.formats['header'])
        worksheet.merge_range(f'A{row}:G{row}', "Live report structure based on your decisions", self.formats['data_cell'])
        row += 1
        
        # Executive Summary
        worksheet.write(row, 0, "📊 EXECUTIVE SUMMARY", self.formats['strength'])
        worksheet.write(row, 1, "Key insights and strategic implications", self.formats['data_cell'])
        worksheet.write(row, 2, "2 pages", self.formats['data_cell'])
        worksheet.write(row, 3, "AUTO-GENERATED", self.formats['validated'])
        worksheet.write(row, 4, "Based on FEATURED themes", self.formats['data_cell'])
        row += 1
        
        # Win Drivers
        worksheet.write(row, 0, "🟢 WIN DRIVERS", self.formats['strength'])
        worksheet.write(row, 1, "Validated themes explaining why customers choose you", self.formats['data_cell'])
        worksheet.write(row, 2, "3-4 pages", self.formats['data_cell'])
        worksheet.write(row, 3, "AUTO-GENERATED", self.formats['validated'])
        worksheet.write(row, 4, "Based on VALIDATED win themes", self.formats['data_cell'])
        row += 1
        
        # Loss Factors
        worksheet.write(row, 0, "🔴 LOSS FACTORS", self.formats['weakness'])
        worksheet.write(row, 1, "Validated themes explaining why customers choose competitors", self.formats['data_cell'])
        worksheet.write(row, 2, "2-3 pages", self.formats['data_cell'])
        worksheet.write(row, 3, "AUTO-GENERATED", self.formats['validated'])
        worksheet.write(row, 4, "Based on VALIDATED loss themes", self.formats['data_cell'])
        row += 1
        
        # Competitive Intelligence
        worksheet.write(row, 0, "🟡 COMPETITIVE INTELLIGENCE", self.formats['mixed_signal'])
        worksheet.write(row, 1, "Validated themes about competitive positioning", self.formats['data_cell'])
        worksheet.write(row, 2, "2-3 pages", self.formats['data_cell'])
        worksheet.write(row, 3, "AUTO-GENERATED", self.formats['validated'])
        worksheet.write(row, 4, "Based on VALIDATED competitive themes", self.formats['data_cell'])
        row += 1
        
        # Implementation Insights
        worksheet.write(row, 0, "🔧 IMPLEMENTATION INSIGHTS", self.formats['mixed_signal'])
        worksheet.write(row, 1, "Validated themes about implementation process", self.formats['data_cell'])
        worksheet.write(row, 2, "1-2 pages", self.formats['data_cell'])
        worksheet.write(row, 3, "AUTO-GENERATED", self.formats['validated'])
        worksheet.write(row, 4, "Based on VALIDATED implementation themes", self.formats['data_cell'])
        row += 2
        
        # Design Handoff Section
        worksheet.write(row, 0, "📤 DESIGN HANDOFF:", self.formats['header'])
        worksheet.merge_range(f'A{row}:G{row}', "Instructions for design team", self.formats['data_cell'])
        row += 1
        
        instructions = [
            "1. Review validated themes in the decision table above",
            "2. Use the report outline structure for content planning", 
            "3. Include featured themes in executive summary",
            "4. Create visual elements based on theme types",
            "5. Use page counts for design specifications"
        ]
        
        for instruction in instructions:
            worksheet.write(row, 0, instruction, self.formats['data_cell'])
            row += 1

    def _get_featured_quotes_from_validated_themes(self, themes_data: Dict[str, Any]) -> List[Dict]:
        """Get featured quotes from validated themes for executive summary"""
        featured_quotes = []
        
        for theme in themes_data['themes']:
            # For now, we'll simulate validated themes (in real implementation, this would read analyst decisions)
            # In a real system, this would check if theme was marked as 'VALIDATED' in section tabs
            if theme.get('theme_type') in ['strength', 'opportunity']:  # Simulate validated win themes
                all_quotes = theme.get('all_quotes', [])
                for quote in all_quotes:
                    # Simulate featured quote classification (in real implementation, this would read from section tabs)
                    if quote.get('impact_score', 0) >= 4:  # High impact quotes as featured
                        quote_with_theme = quote.copy()
                        quote_with_theme['theme_statement'] = theme.get('theme_statement', 'No statement')
                        featured_quotes.append(quote_with_theme)
        
        return featured_quotes[:10]  # Return top 10 featured quotes
    
    def _get_validated_themes_by_section(self, themes_data: Dict[str, Any], section_type: str) -> List[Dict]:
        """Get validated themes for a specific report section"""
        # For now, simulate validated themes based on theme type
        # In real implementation, this would read analyst decisions from section tabs
        section_themes = self._filter_themes_by_section(themes_data['themes'], section_type)
        
        # Simulate validation - in real system, this would check analyst decisions
        validated_themes = []
        for theme in section_themes:
            # Simulate validation based on quality score
            if theme.get('validation_metrics', {}).get('quality_score', 0) >= 7.0:
                validated_themes.append(theme)
        
        return validated_themes
    
    def _get_primary_quotes_for_theme(self, theme: Dict[str, Any]) -> List[Dict]:
        """Get primary quotes for a specific theme"""
        all_quotes = theme.get('all_quotes', [])
        primary_quotes = []
        
        for quote in all_quotes:
            # Simulate primary quote classification (in real implementation, this would read from section tabs)
            if quote.get('impact_score', 0) >= 3:  # Medium-high impact quotes as primary
                primary_quotes.append(quote)
        
        return primary_quotes[:3]  # Return top 3 primary quotes
    
    def _generate_decision_summary(self, themes_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Generate summary of analyst decisions across all sections"""
        sections = {
            'Win Drivers': 'win',
            'Loss Factors': 'loss', 
            'Competitive Intelligence': 'competitive',
            'Implementation Insights': 'implementation'
        }
        
        summary = {}
        for section_name, section_type in sections.items():
            themes = self._filter_themes_by_section(themes_data['themes'], section_type)
            
            # Simulate decision counts (in real implementation, this would read analyst decisions)
            validated = len([t for t in themes if t.get('validation_metrics', {}).get('quality_score', 0) >= 7.0])
            rejected = len([t for t in themes if t.get('validation_metrics', {}).get('quality_score', 0) < 5.0])
            revised = len([t for t in themes if 5.0 <= t.get('validation_metrics', {}).get('quality_score', 0) < 7.0])
            
            # Count featured and primary quotes
            featured_quotes = 0
            primary_quotes = 0
            for theme in themes:
                all_quotes = theme.get('all_quotes', [])
                for quote in all_quotes:
                    if quote.get('impact_score', 0) >= 4:
                        featured_quotes += 1
                    elif quote.get('impact_score', 0) >= 3:
                        primary_quotes += 1
            
            total_themes = len(themes)
            coverage = round((validated / total_themes * 100) if total_themes > 0 else 0, 1)
            
            summary[section_name] = {
                'validated': validated,
                'rejected': rejected,
                'revised': revised,
                'featured_quotes': featured_quotes,
                'primary_quotes': primary_quotes,
                'coverage': coverage
            }
        
        return summary
    
    def _get_quote_research_alignment(self, quote: Dict[str, Any]) -> str:
        """Get research alignment summary for a quote"""
        try:
            # Check if quote has research question alignment data
            if 'research_question_alignment' in quote and quote['research_question_alignment']:
                alignments = quote['research_question_alignment']
                
                if isinstance(alignments, str):
                    try:
                        alignments = json.loads(alignments)
                    except:
                        return "No alignment data"
                
                if alignments:
                    # Gate and present alignment as secondary to DB question
                    alignment_summaries = []
                    # Only include up to 2 suggestions above threshold
                    THRESH = 3  # out of 5
                    for alignment in alignments:
                        score = alignment.get('alignment_score', 0)
                        if score < THRESH:
                            continue
                        question_text_full = alignment.get('question_text', '')
                        question_text = question_text_full[:30] + "..." if len(question_text_full) > 30 else question_text_full
                        priority = alignment.get('coverage_priority', 'medium')
                        alignment_summaries.append(f"{question_text} ({score}/5, {priority})")
                        if len(alignment_summaries) >= 2:
                            break
                    return "; ".join(alignment_summaries) if alignment_summaries else "None"
            
            return "None"
            
        except Exception as e:
            return "Error parsing alignment"
    
    def _create_research_question_alignment_tab(self, themes_data: Dict[str, Any]):
        """Create research question alignment analysis tab"""
        worksheet = self.workbook.add_worksheet('Research Question Alignment')
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Response ID
        worksheet.set_column('B:B', 50)  # Response Text
        worksheet.set_column('C:C', 20)  # Sentiment
        worksheet.set_column('D:D', 15)  # Impact Score
        worksheet.set_column('E:E', 20)  # Harmonized Subject
        worksheet.set_column('F:F', 50)  # Research Questions Addressed
        worksheet.set_column('G:G', 15)  # Questions Count
        worksheet.set_column('H:H', 30)  # Coverage Summary
        worksheet.set_column('I:I', 20)  # Company
        worksheet.set_column('J:J', 20)  # Interviewee
        
        # Title
        worksheet.merge_range('A1:J1', "Research Question Alignment Analysis", self.formats['title'])
        worksheet.merge_range('A2:J2', "How well do individual responses address research questions?", self.formats['subheader'])
        
        # Headers
        headers = [
            "Response ID", "Response Text", "Sentiment", "Impact Score", "Harmonized Subject",
            "Research Questions Addressed", "Questions Count", "Coverage Summary", "Company", "Interviewee"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, self.formats['header'])
        
        # Get responses with research question alignment
        responses = self._get_responses_with_research_alignment()
        
        # Populate data
        row = 4
        for response in responses:
            # Response ID
            worksheet.write(row, 0, response.get('response_id', ''), self.formats['data_cell'])
            
            # Response Text (truncated)
            response_text = response.get('verbatim_response', '')[:100] + "..." if len(response.get('verbatim_response', '')) > 100 else response.get('verbatim_response', '')
            worksheet.write(row, 1, response_text, self.formats['data_cell'])
            
            # Sentiment
            sentiment = response.get('sentiment', 'unknown').title()
            worksheet.write(row, 2, sentiment, self.formats['data_cell'])
            
            # Impact Score
            impact_score = response.get('impact_score', 0)
            worksheet.write(row, 3, impact_score, self.formats['number'])
            
            # Harmonized Subject
            worksheet.write(row, 4, response.get('harmonized_subject', ''), self.formats['data_cell'])
            
            # Research Questions Addressed
            alignments = response.get('research_question_alignment', [])
            if alignments:
                question_texts = []
                for alignment in alignments:
                    question_text = alignment.get('question_text', '')[:40] + "..." if len(alignment.get('question_text', '')) > 40 else alignment.get('question_text', '')
                    score = alignment.get('alignment_score', 0)
                    priority = alignment.get('coverage_priority', 'medium')
                    question_texts.append(f"{question_text} ({score}/5, {priority})")
                questions_text = "; ".join(question_texts)
            else:
                questions_text = "No alignments found"
            worksheet.write(row, 5, questions_text, self.formats['data_cell'])
            
            # Questions Count
            worksheet.write(row, 6, len(alignments), self.formats['number'])
            
            # Coverage Summary
            worksheet.write(row, 7, response.get('coverage_summary', ''), self.formats['data_cell'])
            
            # Company
            worksheet.write(row, 8, response.get('company', ''), self.formats['data_cell'])
            
            # Interviewee
            worksheet.write(row, 9, response.get('interviewee_name', ''), self.formats['data_cell'])
            
            row += 1
        
        # Add summary statistics
        row += 2
        worksheet.write(row, 0, "Alignment Summary", self.formats['header'])
        row += 1
        
        total_responses = len(responses)
        responses_with_alignments = len([r for r in responses if r.get('research_question_alignment')])
        avg_questions_addressed = sum(len(r.get('research_question_alignment', [])) for r in responses) / max(1, total_responses)
        
        worksheet.write(row, 0, "Total Responses:")
        worksheet.write(row, 1, total_responses, self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Responses with Alignments:")
        worksheet.write(row, 1, responses_with_alignments, self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Average Questions Addressed:")
        worksheet.write(row, 1, f"{avg_questions_addressed:.1f}", self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Alignment Rate:")
        worksheet.write(row, 1, f"{(responses_with_alignments / max(1, total_responses)) * 100:.1f}%", self.formats['data_cell'])
    
    def _get_responses_with_research_alignment(self) -> List[Dict]:
        """Get responses that have research question alignment data"""
        try:
            # Get responses from database
            df = self.db.get_stage1_data_responses(client_id=self.client_id)
            
            if df.empty:
                return []
            
            # Filter for responses with research question alignment
            responses_with_alignment = []
            
            for _, row in df.iterrows():
                response_data = row.to_dict()
                
                # Check if response has research question alignment
                if 'research_question_alignment' in response_data and response_data['research_question_alignment']:
                    try:
                        # Parse JSON alignment data
                        if isinstance(response_data['research_question_alignment'], str):
                            alignments = json.loads(response_data['research_question_alignment'])
                        else:
                            alignments = response_data['research_question_alignment']
                        
                        response_data['research_question_alignment'] = alignments
                        responses_with_alignment.append(response_data)
                    except:
                        # Skip if JSON parsing fails
                        continue
            
            return responses_with_alignment
            
        except Exception as e:
            logger.error(f"❌ Failed to get responses with research alignment: {e}")
            return []
    
    def _create_research_question_coverage_tab(self, themes_data: Dict[str, Any]):
        """Create Research Question Coverage using DB-backed research themes and evidence.
        Layout:
          - Column A: Guide Question (Final) in guide order (shown once per question block)
          - Column B: Research Theme (one per theme; shown on the first evidence row for that theme)
          - Column C: Verbatim Quote (one row per supporting quote)
        """
        worksheet = self.workbook.add_worksheet('Research Themes')

        # Column widths
        worksheet.set_column('A:A', 60)   # Guide Question (Final)
        worksheet.set_column('B:B', 80)   # Theme (Research)
        worksheet.set_column('C:C', 16)   # Theme ID
        worksheet.set_column('D:D', 70)   # DB Question (Raw)
        worksheet.set_column('E:E', 12)   # Mapping Confidence
        worksheet.set_column('F:F', 120)  # Verbatim Quote (wider)
        worksheet.set_column('G:G', 22)   # Company
        worksheet.set_column('H:H', 24)   # Interviewee
        worksheet.set_column('I:I', 12)   # Sentiment
        worksheet.set_column('J:J', 14)   # Deal Status
        worksheet.set_column('K:K', 16)   # Quote Classification

        # Title
        worksheet.merge_range('A1:H1', "Research Themes (Guide-seeded themes with supporting quotes)", self.formats['title'])
        worksheet.merge_range('A2:H2', "Questions in guide order. Each row: a supporting verbatim with context for fast analyst review.", self.formats['subheader'])

        # Headers
        row = 4
        headers = ["Guide Question (Final)", "Theme (Research)", "Theme ID", "DB Question (Raw)", "Mapping Confidence", "Verbatim Quote", "Company", "Interviewee", "Sentiment", "Deal Status", "Quote Classification"]
        for col, h in enumerate(headers):
            worksheet.write(row, col, h, self.formats['header'])
        row += 1

        # Quote Classification dropdown (inline list) for all rows in column H
        try:
            worksheet.data_validation(5, 8, 10000, 8, {
                'validate': 'list',
                'source': ['Featured', 'Supporting', 'Exclude']
            })
        except Exception:
            pass

        # Source data
        research_questions: List[str] = self.discussion_guide or []
        # Build question mapping context for filtering evidence to the correct guide question
        self._build_question_map()

        # Per-question retrieval scoring helper (intent-first + token overlap)
        def _score_pair(db_q_text: str, gq_text: str) -> float:
            db_q_text = (db_q_text or '').strip()
            gq_text = (gq_text or '').strip()
            if not db_q_text or not gq_text:
                return 0.0
            norm_db = self._normalize(db_q_text)
            norm_db = ''.join(ch for ch in norm_db if ch.isalnum() or ch.isspace())
            ngq = self._normalize(gq_text)
            ngq = ''.join(ch for ch in ngq if ch.isalnum() or ch.isspace())
            stop = {"can","you","your","about","tell","me","walk","through","share","as","was","it","that","how","what","would","to","the","and","or","a","of","for","just","maybe","well","like"}
            db_tokens_all = set(norm_db.split())
            gq_tokens_all = set(ngq.split())
            db_tokens = {t for t in db_tokens_all if t and t not in stop}
            gq_tokens = {t for t in gq_tokens_all if t and t not in stop}
            if not db_tokens or not gq_tokens:
                return 0.0
            inter = len(db_tokens & gq_tokens)
            union = max(len(db_tokens | gq_tokens), 1)
            score = inter / union
            comp_keywords = {"competitor","competitors","compare","compared","versus","vs","strength","strengths","weakness","weaknesses"}
            if (db_tokens_all & comp_keywords) and (gq_tokens_all & comp_keywords):
                score += 0.2
            if ("introduce" in norm_db or "your role" in norm_db) and ("firm" in norm_db or "attorneys" in norm_db or "support" in norm_db or "size" in norm_db):
                if ("introduce" in ngq) or ("to start" in ngq) or ("describe your role" in ngq):
                    score = max(score, 0.9)
            if ('rated' in ngq and 'pricing' in ngq) and ('rating' in norm_db or 'rated' in norm_db or 'pricing' in norm_db):
                score = max(score, 0.6)
            if (('prompted' in ngq or 'pain' in ngq) and (('pain point' in norm_db) or ('prompt' in norm_db))):
                score = max(score, 0.7)
            if (('implementation' in ngq or 'onboarding' in ngq or 'experience' in ngq) and ('experience' in norm_db or 'implementation' in norm_db or 'onboarding' in norm_db)):
                score = max(score, 0.6)
            return float(min(score, 1.0))

        # Pull DB-backed research themes and evidence
        try:
            rt_res = self.db.supabase.table('research_themes').select('*').eq('client_id', self.client_id).eq('origin', 'research').execute()
            themes_db: List[Dict[str, Any]] = rt_res.data or []
        except Exception:
            themes_db = []
        # Collect theme IDs for scoped evidence retrieval
        theme_ids: List[str] = []
        for t in themes_db:
            tid = t.get('theme_id')
            if tid is not None:
                theme_ids.append(str(tid))
        try:
            # Prefer filtering by theme_id set; avoid client_id filter if table lacks that column
            evidence_db: List[Dict[str, Any]] = []
            if theme_ids:
                try:
                    ev_res = self.db.supabase.table('research_theme_evidence').select('*').in_('theme_id', theme_ids).execute()
                    evidence_db = ev_res.data or []
                except Exception:
                    ev_res2 = self.db.supabase.table('research_theme_evidence').select('*').in_('research_theme_id', theme_ids).execute()
                    evidence_db = ev_res2.data or []
            else:
                ev_res = self.db.supabase.table('research_theme_evidence').select('*').execute()
                evidence_db = ev_res.data or []
        except Exception:
            evidence_db = []
        try:
            quotes_df = self.db.get_stage1_data_responses(client_id=self.client_id)
        except Exception:
            quotes_df = None

        # Build maps
        by_question: Dict[str, List[Dict[str, Any]]] = {q: [] for q in research_questions}
        for t in themes_db:
            qtxt = (t.get('question_text') or '').strip()
            # map by exact normalized string to guide question with canonicalization
            canon = getattr(self, '_guide_canonical_map', {})
            target_q = None
            for gq in research_questions:
                if (gq or '').strip().lower() == qtxt.lower():
                    target_q = canon.get(gq, gq)
                    break
            if not target_q and canon:
                # attempt loose canonical match via key function
                def _dg_key(q: str) -> str:
                    qn = (q or '').strip().lower()
                    qn = ''.join(ch for ch in qn if ch.isalnum() or ch.isspace())
                    return ' '.join(qn.split())
                qtkey = _dg_key(qtxt)
                for gq in research_questions:
                    if _dg_key(gq) == qtkey:
                        target_q = canon.get(gq, gq)
                        break
            if target_q:
                by_question[target_q].append(t)

        evidence_by_theme: Dict[str, List[str]] = {}
        for e in evidence_db:
            tid = e.get('theme_id') or e.get('research_theme_id')
            rid = e.get('response_id')
            if tid and rid:
                evidence_by_theme.setdefault(str(tid), []).append(str(rid))

        quote_text_by_id: Dict[str, str] = {}
        company_by_id: Dict[str, str] = {}
        interviewee_by_id: Dict[str, str] = {}
        sentiment_by_id: Dict[str, str] = {}
        deal_by_id: Dict[str, str] = {}
        subject_by_id: Dict[str, str] = {}
        impact_by_id: Dict[str, float] = {}
        db_q_by_id: Dict[str, str] = {}
        mapped_gq_by_id: Dict[str, str] = {}
        if quotes_df is not None and not quotes_df.empty:
            for _, r in quotes_df.iterrows():
                rid = r.get('response_id')
                if rid is None:
                    continue
                rid_s = str(rid)
                quote_text_by_id[rid_s] = r.get('verbatim_response', '')
                company_by_id[rid_s] = r.get('company') or r.get('company_name', '')
                interviewee_by_id[rid_s] = r.get('interviewee_name', '')
                sentiment_by_id[rid_s] = r.get('sentiment', '')
                deal_by_id[rid_s] = r.get('deal_status') or r.get('deal_outcome', '')
                subject_by_id[rid_s] = r.get('harmonized_subject', '')
                db_q_by_id[rid_s] = (r.get('question', '') or '')
                try:
                    impact_by_id[rid_s] = float(r.get('impact_score', 0) or 0)
                except Exception:
                    impact_by_id[rid_s] = 0.0
            # Build mapped guide question per response for filtering
            for _rid, _dbq in db_q_by_id.items():
                try:
                    _mapped, _, _ = self._map_db_question_to_guide(_dbq)
                except Exception:
                    _mapped = ''
                mapped_gq_by_id[_rid] = _mapped

        # Build labeled headline per theme: "Headline [Strength/Weakness/Mixed • Topic]"
        from collections import Counter
        def _make_headline(raw: str) -> str:
            txt = (raw or '').strip()
            # Keep concise but allow up to 140 chars to avoid over-truncation in workbook
            if len(txt) > 140:
                txt = txt[:137].rstrip() + '…'
            return txt

        theme_label_by_id: Dict[str, str] = {}
        theme_top_subject: Dict[str, str] = {}
        research_display_id_by_tid: Dict[str, str] = {}
        for idx, t in enumerate(themes_db, start=1):
            tid = str(t.get('theme_id', ''))
            if not tid:
                continue
            rids = [str(x) for x in evidence_by_theme.get(tid, [])]
            if not rids:
                theme_label_by_id[tid] = _make_headline(t.get('theme_statement', ''))
                continue
            pos = neg = 0.0
            subs = Counter()
            for rid in rids:
                imp = impact_by_id.get(rid, 0.0)
                sent = (sentiment_by_id.get(rid, '') or '').lower()
                if sent == 'positive':
                    pos += max(imp, 1.0)
                elif sent == 'negative':
                    neg += max(imp, 1.0)
                subj = (subject_by_id.get(rid, '') or '').strip()
                if subj:
                    subs[subj] += 1
            if pos > neg:
                badge = 'Strength'
            elif neg > pos:
                badge = 'Weakness'
            else:
                badge = 'Mixed'
            topic = (subs.most_common(1)[0][0] if subs else 'General')
            headline = _make_headline(t.get('theme_statement', ''))
            theme_label_by_id[tid] = f"{headline} [{badge} • {topic}]"
            theme_top_subject[tid] = topic
            research_display_id_by_tid[tid] = f"research_theme_{idx:03d}"

        # Emit rows in guide order
        for gq in research_questions:
            base_themes_for_q = by_question.get(gq, [])
            # Augment: include any research theme that has evidence rids mapped to this guide question
            augmented = []
            seen_tids = set()
            for t in themes_db:
                tid = str(t.get('theme_id') or '')
                if not tid:
                    continue
                rids = evidence_by_theme.get(tid, [])
                if any((mapped_gq_by_id.get(str(rid), '') or '').strip() == gq.strip() for rid in rids):
                    if tid not in seen_tids:
                        augmented.append(t)
                        seen_tids.add(tid)
            # Merge and dedupe (preserve base order)
            themes_for_gq = base_themes_for_q + [t for t in augmented if t not in base_themes_for_q]
            # Also gather all mapped responses for this guide question
            mapped_rids_for_q = [rid for rid, mgq in mapped_gq_by_id.items() if (mgq or '').strip() == gq.strip()]
            if not themes_for_gq and not mapped_rids_for_q:
                # Show placeholder row for uncovered question
                worksheet.write(row, 0, gq, self.formats['data_cell'])
                worksheet.write(row, 1, '', self.formats['data_cell'])
                worksheet.write(row, 2, '', self.formats['data_cell'])
                worksheet.write(row, 3, '', self.formats['data_cell'])
                worksheet.write(row, 4, '', self.formats['data_cell'])
                worksheet.write(row, 5, '', self.formats['data_cell'])
                worksheet.write(row, 6, '', self.formats['data_cell'])
                worksheet.write(row, 7, '', self.formats['data_cell'])
                row += 1
                continue

            wrote_question_for_block = False
            wrote_header_once = False
            # First, emit evidence rows organized by themes (if any)
            for t in themes_for_gq:
                tid = str(t.get('theme_id') or '')
                stmt = t.get('theme_statement', '')
                rids = evidence_by_theme.get(tid, [])
                if not rids:
                    # Theme without evidence rows; still show the theme line (headline + badges)
                    worksheet.write(row, 0, gq if not wrote_header_once else '', self.formats['data_cell'])
                    worksheet.write(row, 1, theme_label_by_id.get(tid, _make_headline(stmt)), self.formats['data_cell'])
                    worksheet.write(row, 2, '', self.formats['data_cell'])
                    worksheet.write(row, 3, '', self.formats['data_cell'])
                    worksheet.write(row, 4, '', self.formats['data_cell'])
                    worksheet.write(row, 5, '', self.formats['data_cell'])
                    worksheet.write(row, 6, '', self.formats['data_cell'])
                    worksheet.write(row, 7, '', self.formats['data_cell'])
                    row += 1
                    wrote_question_for_block = True
                    continue

                wrote_theme_for_block = False
                for rid in rids:
                    rid_s = str(rid)
                    # Only include evidence if the response maps to this guide question
                    mapped_for_resp = mapped_gq_by_id.get(rid_s, '')
                    if (mapped_for_resp or '').strip() != gq.strip():
                        continue
                    quote_text = quote_text_by_id.get(rid_s, '')
                    company = company_by_id.get(rid_s, '')
                    interviewee = interviewee_by_id.get(rid_s, '')
                    sentiment = sentiment_by_id.get(rid_s, '')
                    deal = deal_by_id.get(rid_s, '')
                    worksheet.write(row, 0, gq, self.formats['data_cell'])
                    # Always render concise headline+badges in Column B on each evidence row
                    worksheet.write(row, 1, theme_label_by_id.get(tid, _make_headline(stmt)), self.formats['data_cell'])
                    worksheet.write(row, 2, research_display_id_by_tid.get(tid, ''), self.formats['data_cell'])
                    worksheet.write(row, 3, db_q_by_id.get(rid_s, ''), self.formats['data_cell'])
                    # Mapping Confidence for theme evidence rows is taken from per-response mapping
                    worksheet.write_number(row, 4, float(self._map_db_question_to_guide(db_q_by_id.get(rid_s, ''))[2]) if db_q_by_id.get(rid_s, '') else 0.0, self.formats['number'])
                    worksheet.write(row, 5, quote_text, self.formats['data_cell'])
                    worksheet.write(row, 6, company, self.formats['data_cell'])
                    worksheet.write(row, 7, interviewee, self.formats['data_cell'])
                    worksheet.write(row, 8, sentiment, self.formats['data_cell'])
                    worksheet.write(row, 9, deal, self.formats['data_cell'])
                    worksheet.write(row, 10, '', self.formats['data_cell'])
                    row += 1
                    wrote_header_once = True
                    wrote_theme_for_block = True

            # separator line between questions
            worksheet.write(row, 0, '', self.formats['data_cell'])
            row += 1
            # Emit remaining mapped responses (not tied to any theme) with Theme inferred where possible
            remaining = [rid for rid, mgq in mapped_gq_by_id.items() if (mgq or '').strip() == gq.strip()]
            if remaining:
                themed_rids = set()
                for t in themes_for_gq:
                    tid2 = str(t.get('theme_id') or '')
                    themed_rids.update(str(r) for r in evidence_by_theme.get(tid2, []) or [])
                wrote_question_for_block2 = False
                wrote_header_once = True  # ensure we don't reprint header in remaining block
                # Build a lightweight assignment map for remaining quotes → best theme (if any)
                assignments: Dict[str, str] = {}
                if len(themes_for_gq) == 1:
                    only_tid = str(themes_for_gq[0].get('theme_id') or '')
                    for rid_s in remaining:
                        if rid_s not in themed_rids:
                            assignments[rid_s] = only_tid
                else:
                    # subject-first, then simple similarity on lowercase token overlap
                    def _sim(a: str, b: str) -> float:
                        at = set((a or '').lower().split())
                        bt = set((b or '').lower().split())
                        if not at or not bt:
                            return 0.0
                        inter = len(at & bt)
                        union = max(len(at | bt), 1)
                        return inter / union
                    for rid_s in remaining:
                        if rid_s in themed_rids:
                            continue
                        qtxt = quote_text_by_id.get(rid_s, '')
                        qsubj = (subject_by_id.get(rid_s, '') or '').strip()
                        best_tid = ''
                        best_score = 0.0
                        for t in themes_for_gq:
                            tid2 = str(t.get('theme_id') or '')
                            stmt = t.get('theme_statement', '')
                            s = _sim(qtxt, stmt)
                            if qsubj and qsubj == (theme_top_subject.get(tid2) or ''):
                                s += 0.15
                            if s > best_score:
                                best_score = s
                                best_tid = tid2
                        if best_tid and best_score >= 0.1:
                            assignments[rid_s] = best_tid
                for rid_s in remaining:
                    if rid_s in themed_rids:
                        continue
                    # Print the Guide Question on every remaining evidence row
                    worksheet.write(row, 0, gq, self.formats['data_cell'])
                    # Fill Theme using assignment if available
                    tid_assigned = assignments.get(rid_s, '')
                    if tid_assigned:
                        worksheet.write(row, 1, theme_label_by_id.get(tid_assigned, ''), self.formats['data_cell'])
                        worksheet.write(row, 2, research_display_id_by_tid.get(tid_assigned, ''), self.formats['data_cell'])
                    else:
                        worksheet.write(row, 1, '', self.formats['data_cell'])
                        worksheet.write(row, 2, '', self.formats['data_cell'])
                    worksheet.write(row, 3, db_q_by_id.get(rid_s, ''), self.formats['data_cell'])
                    worksheet.write_number(row, 4, float(self._map_db_question_to_guide(db_q_by_id.get(rid_s, ''))[2]) if db_q_by_id.get(rid_s, '') else 0.0, self.formats['number'])
                    worksheet.write(row, 5, quote_text_by_id.get(rid_s, ''), self.formats['data_cell'])
                    worksheet.write(row, 6, company_by_id.get(rid_s, ''), self.formats['data_cell'])
                    worksheet.write(row, 7, interviewee_by_id.get(rid_s, ''), self.formats['data_cell'])
                    worksheet.write(row, 8, sentiment_by_id.get(rid_s, ''), self.formats['data_cell'])
                    worksheet.write(row, 9, deal_by_id.get(rid_s, ''), self.formats['data_cell'])
                    worksheet.write(row, 10, '', self.formats['data_cell'])
                    row += 1
                    wrote_question_for_block2 = True
                worksheet.write(row, 0, '', self.formats['data_cell'])
                row += 1

            # Retrieval augmentation: if mapped coverage is sparse, pull top-scored responses for this guide question
            try:
                MIN_ROWS_PER_Q = 8
                current_count = len([rid for rid, mgq in mapped_gq_by_id.items() if (mgq or '').strip() == gq.strip()])
                if current_count < MIN_ROWS_PER_Q and quotes_df is not None and not quotes_df.empty:
                    scores = []
                    for rid_s, dbq in db_q_by_id.items():
                        if not dbq:
                            continue
                        s = _score_pair(dbq, gq)
                        if s <= 0:
                            continue
                        scores.append((s, rid_s))
                    already = set([rid for rid, mgq in mapped_gq_by_id.items() if (mgq or '').strip() == gq.strip()])
                    for t in themes_for_q:
                        tid2 = str(t.get('theme_id') or '')
                        already.update(str(r) for r in evidence_by_theme.get(tid2, []) or [])
                    scores.sort(key=lambda x: (-x[0], -impact_by_id.get(x[1], 0.0), company_by_id.get(x[1], '')))
                    need = MIN_ROWS_PER_Q - current_count
                    added = 0
                    wrote_header = False
                    for s, rid_s in scores:
                        if rid_s in already:
                            continue
                        if added >= need:
                            break
                        worksheet.write(row, 0, gq, self.formats['data_cell'])
                        worksheet.write(row, 1, '', self.formats['data_cell'])
                        worksheet.write(row, 2, db_q_by_id.get(rid_s, ''), self.formats['data_cell'])
                        worksheet.write_number(row, 3, s, self.formats['number'])
                        worksheet.write(row, 4, quote_text_by_id.get(rid_s, ''), self.formats['data_cell'])
                        worksheet.write(row, 5, company_by_id.get(rid_s, ''), self.formats['data_cell'])
                        worksheet.write(row, 6, interviewee_by_id.get(rid_s, ''), self.formats['data_cell'])
                        worksheet.write(row, 7, sentiment_by_id.get(rid_s, ''), self.formats['data_cell'])
                        worksheet.write(row, 8, deal_by_id.get(rid_s, ''), self.formats['data_cell'])
                        worksheet.write(row, 9, '', self.formats['data_cell'])
                        row += 1
                        wrote_header = True
                        added += 1
                    if added:
                        worksheet.write(row, 0, '', self.formats['data_cell'])
                        row += 1
            except Exception:
                pass

    def _analyze_theme_question_coverage(self, themes: List[Dict], research_questions: List[str]) -> Dict[str, Any]:
        """Analyze how well themes cover research questions"""
        
        coverage_analysis = {
            'question_coverage': {},
            'uncovered_questions': [],
            'questions_with_coverage': 0,
            'coverage_percentage': 0
        }
        
        # Initialize question coverage
        for question in research_questions:
            coverage_analysis['question_coverage'][question] = {
                'themes': [],
                'evidence_strength': 0,
                'coverage_score': 0
            }
        
        # Analyze each theme against research questions
        for theme in themes:
            theme_text = f"{theme.get('theme_statement', '')} {theme.get('harmonized_subject', '')}".lower()
            theme_type = theme.get('theme_type', '').lower()
            
            # Check alignment with each research question
            for question in research_questions:
                question_lower = question.lower()
                
                # Enhanced matching logic
                matches = self._check_question_theme_alignment(question_lower, theme_text, theme_type)
                
                if matches:
                    alignment_score = len(matches) / max(len(self._extract_question_keywords(question_lower)), 1)
                    if alignment_score > 0.1:  # Lowered threshold to 10% for better coverage
                        coverage_analysis['question_coverage'][question]['themes'].append(theme)
                        coverage_analysis['question_coverage'][question]['coverage_score'] = max(
                            coverage_analysis['question_coverage'][question]['coverage_score'],
                            alignment_score
                        )
        
        # Calculate coverage statistics
        for question, coverage in coverage_analysis['question_coverage'].items():
            if coverage['themes']:
                coverage_analysis['questions_with_coverage'] += 1
            else:
                coverage_analysis['uncovered_questions'].append(question)
        
        coverage_analysis['coverage_percentage'] = (
            coverage_analysis['questions_with_coverage'] / len(research_questions)
        ) * 100
        
        return coverage_analysis
    
    def _check_question_theme_alignment(self, question: str, theme_text: str, theme_type: str) -> List[str]:
        """Check if a theme aligns with a specific research question"""
        matches = []
        theme_text_lower = theme_text.lower()
        question_lower = question.lower()
        
        # Special handling for rating questions (e.g., "I see you rated Pricing a #")
        if 'rated' in question_lower and '#' in question_lower:
            # Extract the topic being rated
            if 'pricing' in question_lower:
                rating_topics = ['pricing', 'price', 'cost', 'value', 'expensive', 'cheap', 'affordable']
            elif 'understanding' in question_lower and 'business' in question_lower:
                rating_topics = ['understanding', 'business', 'needs', 'pain', 'requirements']
            elif 'implementation' in question_lower:
                rating_topics = ['implementation', 'onboarding', 'setup', 'deployment', 'process']
            elif 'technology' in question_lower:
                rating_topics = ['technology', 'platform', 'infrastructure', 'robust', 'reliable']
            elif 'functionality' in question_lower:
                rating_topics = ['functionality', 'features', 'capabilities', 'requirements']
            elif 'company alignment' in question_lower or 'culture' in question_lower:
                rating_topics = ['company', 'alignment', 'culture', 'values', 'fit', 'organization']
            else:
                rating_topics = []
            
            for topic in rating_topics:
                if topic in theme_text_lower:
                    matches.append(topic)
        
        # Special handling for evaluation criteria questions
        if 'criteria' in question_lower and 'evaluate' in question_lower:
            evaluation_terms = ['criteria', 'evaluate', 'assessment', 'decision', 'factor', 'consideration', 'requirement', 'need', 'important', 'key']
            for term in evaluation_terms:
                if term in theme_text_lower:
                    matches.append(term)
        
        # Special handling for competitive comparison questions
        if 'strengths' in question_lower and 'versus' in question_lower:
            competitive_terms = ['strength', 'advantage', 'better', 'superior', 'excellent', 'outstanding', 'versus', 'compared']
            for term in competitive_terms:
                if term in theme_text_lower:
                    matches.append(term)
        
        if 'weaknesses' in question_lower and 'versus' in question_lower:
            weakness_terms = ['weakness', 'disadvantage', 'worse', 'inferior', 'problem', 'issue', 'versus', 'compared']
            for term in weakness_terms:
                if term in theme_text_lower:
                    matches.append(term)
        
        # Special handling for implementation questions
        if 'implementation' in question_lower and 'process' in question_lower:
            implementation_terms = ['implementation', 'process', 'onboarding', 'setup', 'deployment', 'experience']
            for term in implementation_terms:
                if term in theme_text_lower:
                    matches.append(term)
        
        # Special handling for sales team questions
        if 'sales team' in question_lower:
            sales_terms = ['sales', 'team', 'representative', 'rep', 'presentation', 'demonstration', 'communication']
            for term in sales_terms:
                if term in theme_text_lower:
                    matches.append(term)
        
        # Special handling for vendor selection questions
        if 'vendors' in question_lower and 'evaluate' in question_lower:
            vendor_terms = ['vendor', 'provider', 'supplier', 'evaluate', 'compare', 'selection', 'choose']
            for term in vendor_terms:
                if term in theme_text_lower:
                    matches.append(term)
        
        # Special handling for prompt questions (what prompted you to evaluate)
        if 'prompted' in question_lower and 'evaluate' in question_lower:
            prompt_terms = ['prompted', 'triggered', 'led', 'caused', 'motivated', 'evaluate', 'consider', 'look']
            for term in prompt_terms:
                if term in theme_text_lower:
                    matches.append(term)
        
        # Special handling for improvement questions
        if 'improve' in question_lower or 'better' in question_lower:
            improvement_terms = ['improve', 'better', 'enhance', 'upgrade', 'fix', 'resolve', 'address']
            for term in improvement_terms:
                if term in theme_text_lower:
                    matches.append(term)
        
        # General keyword matching for other questions (ALWAYS check this as fallback)
        keywords = self._extract_question_keywords(question)
        for keyword in keywords:
            if keyword in theme_text_lower:
                matches.append(keyword)
        
        return matches
    
    def _extract_question_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from research question"""
        # Remove common words and extract keywords
        stop_words = {'what', 'how', 'why', 'when', 'where', 'who', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'you', 'your', 'i', 'me', 'my', 'we', 'our', 'they', 'them', 'their', 'it', 'its', 'if', 'not', 'already', 'mentioned', 'ultimately', 'choose', 'over', 'other', 'versus', 'companies', 'could', 'briefly', 'introduce', 'describe', 'role', 'firm', 'prompted', 'evaluate', 'solutions', 'like', 'key', 'criteria', 'used', 'providers', 'else', 'involved', 'process', 'focus', 'probe', 'paralegals', 'operations', 'technology', 'team', 'members', 'partners', 'client', 'background', 'assumptions', 'stakeholders', 'primary', 'end', 'users', 'often', 'champion', 'profitability', 'outcome', 'uncover', 'reasons', 'winning', 'losing', 'deals', 'gaps', 'product', 'features', 'pricing', 'strategies', 'sales', 'execution', 'effectiveness', 'presentations', 'communicating', 'value', 'addressing', 'needs', 'analyze', 'competitor', 'strengths', 'customer', 'perceptions', 'brand', 'relative', 'inform', 'competitive', 'positioning', 'refine', 'marketing', 'strategies', 'participant', 'name', 'thanks', 'joining', 'interview', 'conducted', 'learn', 'technology', 'experience', 'permission', 'recording', 'conversation', 'transcript', 'report', 'shared', 'materials', 'gain', 'valuable', 'insights', 'consumers', 'questions', 'information', 'concerned', 'anonymity', 'remove', 'mentions', 'company', 'conduct', 'notes', 'background', 'evaluation', 'understand', 'buying', 'decision', 'making', 'vendor', 'selection', 'vendors', 'evaluated', 'ultimately', 'selected', 'win', 'loss', 'choose', 'competitor', 'supio', 'perceptions', 'competitors', 'learn', 'perceived', 'context', 'assumptions', 'tech', 'company', 'purpose', 'built', 'legal', 'human', 'validation', 'speed', 'focused', 'targets', 'smaller', 'firms', 'legal', 'using', 'entering', 'space', 'lighter', 'offering', 'alignment', 'functionality', 'areas', 'improvement', 'messaging', 'positioning', 'typically', 'higher', 'next', 'launch', 'quick', 'poll', 'rate', 'agreement', 'statements', 'scale', 'strongly', 'disagree', 'agree', 'probe', 'reasons', 'behind', 'ratings', 'examples', 'elaborate', 'driving', 'rating', 'compare', 'low', 'could', 'get', 'follow', 'features', 'competitors', 'offered', 'lacked', 'influence', 'impression', 'listen', 'unclear', 'complicated', 'performance', 'dive', 'deeper', 'effectiveness', 'articulate', 'proposition', 'avoid', 'commoditization', 'needs', 'improvement', 'reps', 'recently', 'hired', 'market', 'segmentation', 'strong', 'fit', 'large', 'plaintiff', 'firms', 'good', 'mid', 'size', 'employees', 'model', 'small', 'focus', 'experience', 'team', 'well', 'improve', 'last', 'quick', 'capture', 'feedback', 'criteria', 'poor', 'below', 'average', 'good', 'excellent', 'understanding', 'business', 'pain', 'points', 'knowledge', 'capabilities', 'effective', 'communication', 'value', 'proposition', 'quality', 'demonstrations', 'presentations', 'responsiveness', 'timeliness', 'follow', 'wrap', 'single', 'important', 'thing', 'think', 'focus', 'improve', 'offerings', 'process', 'questions', 'time', 'today'}
        
        # Special handling for rating questions (e.g., "I see you rated Pricing a #")
        if 'rated' in text.lower() and '#' in text:
            # Extract the topic being rated
            if 'pricing' in text.lower():
                rating_topics = ['pricing', 'price', 'cost', 'value', 'expensive', 'cheap', 'affordable']
            elif 'understanding' in text.lower() and 'business' in text.lower():
                rating_topics = ['understanding', 'business', 'needs', 'pain', 'requirements']
            elif 'implementation' in text.lower():
                rating_topics = ['implementation', 'onboarding', 'setup', 'deployment', 'process']
            elif 'technology' in text.lower():
                rating_topics = ['technology', 'platform', 'infrastructure', 'robust', 'reliable']
            elif 'functionality' in text.lower():
                rating_topics = ['functionality', 'features', 'capabilities', 'requirements']
            elif 'company alignment' in text.lower() or 'culture' in text.lower():
                rating_topics = ['company', 'alignment', 'culture', 'values', 'fit', 'organization']
            else:
                rating_topics = []
            
            words = text.split()
            keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 2]
            # Add rating topics if they're in the question
            for topic in rating_topics:
                if topic in text.lower():
                    keywords.append(topic)
            return list(set(keywords))
        
        # Special handling for evaluation criteria questions
        elif 'criteria' in text.lower() and 'evaluate' in text.lower():
            # Extract key evaluation terms
            evaluation_terms = ['criteria', 'evaluate', 'assessment', 'decision', 'factor', 'consideration', 'requirement', 'need', 'important', 'key', 'provider', 'vendor', 'supplier']
            words = text.split()
            keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 2]
            # Add evaluation terms if they're in the question
            for term in evaluation_terms:
                if term in text.lower():
                    keywords.append(term)
            return list(set(keywords))
        
        # Special handling for competitive comparison questions
        elif 'strengths' in text.lower() and 'versus' in text.lower():
            # Extract competitive comparison terms
            competitive_terms = ['strengths', 'versus', 'compared', 'competitor', 'competitive', 'advantage', 'superior']
            words = text.split()
            keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 2]
            # Add competitive terms if they're in the question
            for term in competitive_terms:
                if term in text.lower():
                    keywords.append(term)
            return list(set(keywords))
        
        elif 'weaknesses' in text.lower() and 'versus' in text.lower():
            # Extract weakness comparison terms
            weakness_terms = ['weaknesses', 'versus', 'compared', 'competitor', 'disadvantage', 'inferior', 'problem']
            words = text.split()
            keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 2]
            # Add weakness terms if they're in the question
            for term in weakness_terms:
                if term in text.lower():
                    keywords.append(term)
            return list(set(keywords))
        
        # Special handling for implementation questions
        elif 'implementation' in text.lower() and 'process' in text.lower():
            # Extract implementation terms
            implementation_terms = ['implementation', 'process', 'onboarding', 'setup', 'deployment', 'experience']
            words = text.split()
            keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 2]
            # Add implementation terms if they're in the question
            for term in implementation_terms:
                if term in text.lower():
                    keywords.append(term)
            return list(set(keywords))
        
        # Special handling for sales team questions
        elif 'sales team' in text.lower():
            # Extract sales team terms
            sales_terms = ['sales', 'team', 'representative', 'rep', 'presentation', 'demonstration', 'communication']
            words = text.split()
            keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 2]
            # Add sales terms if they're in the question
            for term in sales_terms:
                if term in text.lower():
                    keywords.append(term)
            return list(set(keywords))
        
        # Special handling for vendor selection questions
        elif 'vendors' in text.lower() and 'evaluate' in text.lower():
            # Extract vendor evaluation terms
            vendor_terms = ['vendors', 'evaluate', 'compare', 'selection', 'choose', 'provider', 'supplier']
            words = text.split()
            keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 2]
            # Add vendor terms if they're in the question
            for term in vendor_terms:
                if term in text.lower():
                    keywords.append(term)
            return list(set(keywords))
        
        # Special handling for prompt questions (what prompted you to evaluate)
        elif 'prompted' in text.lower() and 'evaluate' in text.lower():
            # Extract prompt terms
            prompt_terms = ['prompted', 'triggered', 'led', 'caused', 'motivated', 'evaluate', 'consider', 'look']
            words = text.split()
            keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 2]
            # Add prompt terms if they're in the question
            for term in prompt_terms:
                if term in text.lower():
                    keywords.append(term)
            return list(set(keywords))
        
        # Special handling for improvement questions
        elif 'improve' in text.lower() or 'better' in text.lower():
            # Extract improvement terms
            improvement_terms = ['improve', 'better', 'enhance', 'upgrade', 'fix', 'resolve', 'address']
            words = text.split()
            keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 2]
            # Add improvement terms if they're in the question
            for term in improvement_terms:
                if term in text.lower():
                    keywords.append(term)
            return list(set(keywords))
        
        # General keyword extraction
        else:
            words = text.split()
            keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 3]
            return list(set(keywords))  # Remove duplicates
    
    def _create_discussion_guide_coverage_tab(self, themes_data: Dict[str, Any]):
        """Create discussion guide coverage analysis tab"""
        worksheet = self.workbook.add_worksheet('Discussion Guide Coverage')
        
        # Set column widths
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 60)
        worksheet.set_column('C:C', 20)
        
        # Title
        worksheet.merge_range('A1:C1', "Discussion Guide Coverage Analysis", self.formats['title'])
        worksheet.merge_range('A2:C2', "Analysis of how well themes address original research questions", self.formats['subheader'])
        
        # Import discussion guide integrator
        from discussion_guide_integration import DiscussionGuideIntegrator
        integrator = DiscussionGuideIntegrator()
        
        # Get Supio discussion guide
        if not hasattr(self, 'discussion_guide'):
            from discussion_guide_integration import DiscussionGuideIntegrator
            integrator = DiscussionGuideIntegrator()
            self.discussion_guide = integrator.parse_supio_discussion_guide('uploads/Supio_PRJ-00027 Discussion Guide v1.txt')
        # Canonicalize/dedupe guide here as well
        def _dg_key(q: str) -> str:
            qn = (q or '').strip().lower()
            qn = ''.join(ch for ch in qn if ch.isalnum() or ch.isspace())
            return ' '.join(qn.split())
        _seen = {}
        _deduped = []
        for q in (self.discussion_guide or []):
            k = _dg_key(q)
            if k in _seen:
                continue
            _seen[k] = q
            _deduped.append(q)
        self.discussion_guide = _deduped
        
        discussion_guide = self.discussion_guide
        
        # Analyze coverage
        coverage_analysis = integrator.analyze_coverage(
            self.discussion_guide,
            themes_data['themes']
        )
        
        # Map questions to themes
        question_mappings = integrator.map_questions_to_themes(self.discussion_guide, themes_data['themes'])
        
        # Coverage Summary
        row = 4
        worksheet.write(row, 0, "Coverage Summary", self.formats['header'])
        row += 1
        worksheet.write(row, 0, "Total Questions:")
        worksheet.write(row, 1, coverage_analysis['total_questions'], self.formats['data_cell'])
        row += 1
        worksheet.write(row, 0, "Covered Questions:")
        worksheet.write(row, 1, coverage_analysis['covered_questions'], self.formats['data_cell'])
        row += 1
        worksheet.write(row, 0, "Coverage Percentage:")
        worksheet.write(row, 1, f"{coverage_analysis['coverage_percentage']:.1f}%", self.formats['data_cell'])
        
        # Question Coverage Details
        row += 2
        worksheet.write(row, 0, "Question Coverage Details", self.formats['header'])
        row += 1
        
        for coverage_item in coverage_analysis['coverage_data']:
            question = coverage_item['question']
            theme_count = coverage_item['theme_count']
            status = coverage_item['coverage_status']
            
            if status == 'Covered':
                worksheet.write(row, 0, f"✅ {question}", self.formats['data_cell'])
                worksheet.write(row, 1, f"Addressed by {theme_count} themes", self.formats['data_cell'])
            else:
                worksheet.write(row, 0, f"❌ {question}", self.formats['high_priority'])
                worksheet.write(row, 1, "No themes address this question", self.formats['high_priority'])
            row += 1
        
        # Theme-Question Mapping
        row += 2
        worksheet.write(row, 0, "Theme-Question Mapping", self.formats['header'])
        row += 1
        
        for theme_id, questions in question_mappings.items():
            if questions:
                worksheet.write(row, 0, f"✅ {theme_id}", self.formats['validated'])
                worksheet.write(row, 1, f"Addresses {len(questions)} questions", self.formats['data_cell'])
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
            theme_type = theme.get('theme_type', 'unknown')
            if theme_type not in summaries:
                summaries[theme_type] = {
                    'count': 0,
                    'total_quotes': 0,
                    'avg_quality': 0.0,
                    'companies': set()
                }
            
            summaries[theme_type]['count'] += 1
            summaries[theme_type]['total_quotes'] += theme['validation_metrics'].get('quotes_count', 0)
            summaries[theme_type]['avg_quality'] += theme['validation_metrics'].get('confidence_score', 0.0)
            
            # Add companies
            company_distribution = theme.get('company_distribution', {})
            if 'companies' in company_distribution:
                for company in company_distribution['companies']:
                    summaries[theme_type]['companies'].add(company)
        
        # Calculate averages and insights
        for theme_type, summary in summaries.items():
            if summary['count'] > 0:
                summary['avg_quality_score'] = summary['avg_quality'] / summary['count']
            
            # Generate key insight
            if theme_type == 'strength':
                summary['key_insight'] = f"Identified {summary['count']} competitive advantages"
            elif theme_type == 'weakness':
                summary['key_insight'] = f"Found {summary['count']} areas requiring immediate attention"
            elif theme_type == 'investigation_needed':
                summary['key_insight'] = f"Discovered {summary['count']} complex patterns needing investigation"
            else:
                summary['key_insight'] = f"Identified {summary['count']} {theme_type} themes"
        
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
    
    def _determine_win_loss_category(self, theme: Dict[str, Any]) -> str:
        """Determine win-loss category based on theme type and characteristics"""
        theme_type = theme.get('theme_type', '').lower()
        competitive_flag = theme.get('competitive_flag', False)
        harmonized_subject = theme.get('harmonized_subject', '').lower()
        
        # Map theme types to win-loss categories
        if theme_type == 'strength':
            if competitive_flag or 'competitive' in harmonized_subject:
                return 'Competitive'
            else:
                return 'Strength'
        elif theme_type == 'weakness':
            return 'Weakness'
        elif theme_type in ['opportunity', 'investigation_needed']:
            if 'sales' in harmonized_subject or 'implementation' in harmonized_subject:
                return 'Process'
            elif competitive_flag or 'competitive' in harmonized_subject:
                return 'Competitive'
            else:
                return 'Opportunity'
        else:
            # Default categorization for mixed/other themes
            if competitive_flag or 'competitive' in harmonized_subject:
                return 'Competitive'
            elif 'sales' in harmonized_subject or 'implementation' in harmonized_subject:
                return 'Process'
            else:
                return 'Opportunity'
    
    def _determine_report_section(self, win_loss_category: str) -> str:
        """Map win-loss category to report section"""
        section_mapping = {
            'Strength': 'Section 2: Why You Win',
            'Weakness': 'Section 3: Why You Lose', 
            'Opportunity': 'Section 4: Market Opportunities',
            'Competitive': 'Section 5: Competitive Intelligence',
            'Process': 'Section 6: Implementation Insights'
        }
        return section_mapping.get(win_loss_category, 'Section 4: Market Opportunities')
    
    def _get_research_questions_for_section(self, section_name: str) -> List[str]:
        """Get research questions from the actual discussion guide file"""
        try:
            # Path to the discussion guide
            discussion_guide_path = 'uploads/Supio_PRJ-00027 Discussion Guide v1.txt'
            
            with open(discussion_guide_path, 'r') as f:
                content = f.read()
            
            # Parse the discussion guide to extract questions by section
            questions = self._parse_discussion_guide_for_section(content, section_name)
            
            return questions
            
        except FileNotFoundError:
            print(f"Warning: Discussion guide not found at {discussion_guide_path}")
            # Return empty or default questions as fallback
            return []
        except Exception as e:
            print(f"Error reading discussion guide: {e}")
            return []
    
    def _parse_discussion_guide_for_section(self, content: str, section_name: str) -> List[str]:
        """Parse discussion guide content to extract questions for a specific section"""
        
        questions = []
        lines = content.split('\n')
        in_section = False
        
        # Map section names to discussion guide sections
        section_markers = {
            'Win Drivers': ['Win/Loss Outcome', 'WIN:', 'Why did you ultimately choose Supio'],
            'Loss Factors': ['Win/Loss Outcome', 'LOSS:', 'Why did you ultimately choose'],
            'Competitive Intelligence': ['Supio Perceptions vs Competitors', 'Competitors'],
            'Implementation Insights': ['Implementation Experience', 'Implementation']
        }
        
        target_markers = section_markers.get(section_name, [])
        
        for line in lines:
            line = line.strip()
            
            # Check if we're entering the target section
            for marker in target_markers:
                if marker in line:
                    in_section = True
                    break
            
            # Check if we're leaving the section (entering a new numbered section)
            if in_section and line.startswith(('8.', '9.', '10.', '11.', '12.', '13.', '14.', '15.', '16.')):
                # We've moved to a new section
                break
            
            # Extract questions from the current section
            if in_section and line:
                # Look for question patterns
                if '?' in line and not line.startswith('*') and not line.startswith('CONTEXT:'):
                    # Clean up the question
                    question = line.strip()
                    if question and len(question) > 10:  # Avoid very short lines
                        questions.append(question)
        
        return questions
    
    def _count_evidence_for_research_question(self, question: str) -> int:
        """Count how many responses provide evidence for a specific research question"""
        try:
            df = self.db.get_stage1_data_responses(client_id=self.client_id)
            if df.empty:
                return 0
            
            # Count responses that have research alignment data for this question
            count = 0
            for _, row in df.iterrows():
                if pd.notna(row.get('research_question_alignment')):
                    try:
                        alignments = json.loads(row['research_question_alignment']) if isinstance(row['research_question_alignment'], str) else row['research_question_alignment']
                        for alignment in alignments:
                            if question.lower() in alignment.get('question_text', '').lower():
                                count += 1
                                break
                    except:
                        continue
            
            return count
        except Exception as e:
            logger.error(f"Error counting evidence for question: {e}")
            return 0
    
    def _get_discovered_themes_for_section(self, section_name: str) -> List[Dict]:
        """Get discovered themes for a specific report section"""
        # For now, return sample themes - this would be populated from actual theme analysis
        sample_themes = {
            'Win Drivers': [
                {
                    'theme_id': 'WD001',
                    'theme_statement': 'Product features and capabilities drive vendor selection',
                    'validation_metrics': {'confidence_score': 0.85, 'quotes_count': 15},
                    'research_alignment': 'Strong alignment with product evaluation criteria'
                },
                {
                    'theme_id': 'WD002', 
                    'theme_statement': 'Customer service and support quality',
                    'validation_metrics': {'confidence_score': 0.78, 'quotes_count': 8},
                    'research_alignment': 'Addresses implementation and support concerns'
                }
            ],
            'Loss Factors': [
                {
                    'theme_id': 'LF001',
                    'theme_statement': 'Pricing concerns and budget constraints',
                    'validation_metrics': {'confidence_score': 0.72, 'quotes_count': 12},
                    'research_alignment': 'Directly addresses pricing comparison questions'
                }
            ],
            'Competitive Intelligence': [
                {
                    'theme_id': 'CI001',
                    'theme_statement': 'Competitive positioning and differentiation',
                    'validation_metrics': {'confidence_score': 0.81, 'quotes_count': 10},
                    'research_alignment': 'Covers competitive evaluation and vendor comparison'
                }
            ],
            'Implementation Insights': [
                {
                    'theme_id': 'II001',
                    'theme_statement': 'Implementation process and timeline',
                    'validation_metrics': {'confidence_score': 0.75, 'quotes_count': 6},
                    'research_alignment': 'Addresses implementation experience questions'
                }
            ]
        }
        
        return sample_themes.get(section_name, [])
    
    def _get_theme_research_alignment(self, theme: Dict) -> str:
        """Get research alignment summary for a theme"""
        alignment = theme.get('research_alignment', 'No alignment data')
        return alignment[:50] + "..." if len(alignment) > 50 else alignment
    
    def _get_quotes_for_section(self, section_name: str) -> List[Dict]:
        """Get quotes relevant to a specific report section"""
        try:
            df = self.db.get_stage1_data_responses(client_id=self.client_id)
            if df.empty:
                return []
            
            # Filter quotes based on section relevance
            section_keywords = {
                'Win Drivers': ['strength', 'positive', 'good', 'great', 'excellent', 'value', 'feature', 'capability'],
                'Loss Factors': ['weakness', 'negative', 'bad', 'poor', 'issue', 'problem', 'concern', 'disappointing'],
                'Competitive Intelligence': ['competitor', 'compare', 'versus', 'alternative', 'other', 'different'],
                'Implementation Insights': ['implementation', 'setup', 'process', 'timeline', 'experience', 'support']
            }
            
            keywords = section_keywords.get(section_name, [])
            relevant_quotes = []
            
            for _, row in df.iterrows():
                quote_text = row.get('verbatim_response', '').lower()
                if any(keyword in quote_text for keyword in keywords):
                    relevant_quotes.append(row.to_dict())
            
            return relevant_quotes[:20]  # Limit to 20 most relevant quotes
            
        except Exception as e:
            logger.error(f"Error getting quotes for section: {e}")
            return []

    def _identify_cross_section_themes(self, themes: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Identify themes that appear in multiple sections and map their locations"""
        theme_sections = {}
        
        # Check each theme against all section types
        for theme in themes:
            theme_id = theme.get('theme_id', 'unknown')
            theme_sections[theme_id] = []
            
            # Test against each section type
            for section_type in ['win', 'loss', 'competitive', 'implementation']:
                filtered = self._filter_themes_by_section([theme], section_type)
                if filtered:
                    theme_sections[theme_id].append(section_type)
        
        # Return only themes that appear in multiple sections
        cross_section_themes = {
            theme_id: sections 
            for theme_id, sections in theme_sections.items() 
            if len(sections) > 1
        }
        
        return cross_section_themes
    
    def _get_primary_section_for_theme(self, theme: Dict[str, Any], cross_section_map: Dict[str, List[str]]) -> str:
        """Determine the primary section for a theme to avoid duplication"""
        theme_id = theme.get('theme_id', 'unknown')
        
        if theme_id not in cross_section_map:
            # Single-section theme - use its natural section
            return self._determine_primary_section(theme)
        
        # Cross-section theme - determine primary based on priority
        sections = cross_section_map[theme_id]
        
        # Priority order: win > loss > competitive > implementation
        priority_order = ['win', 'loss', 'competitive', 'implementation']
        
        for section in priority_order:
            if section in sections:
                return section
        
        return sections[0]  # Fallback
    
    def _determine_primary_section(self, theme: Dict[str, Any]) -> str:
        """Determine the primary section for a single-section theme"""
        theme_type = theme.get('theme_type', '').lower()
        subject = theme.get('harmonized_subject', '').lower()
        
        if theme_type == 'strength':
            return 'win'
        elif theme_type == 'weakness':
            return 'loss'
        elif 'competitive' in subject or 'market' in subject:
            return 'competitive'
        elif 'implementation' in subject or 'integration' in subject:
            return 'implementation'
        else:
            # Default based on theme type
            return 'win' if theme_type == 'strength' else 'loss'
    
    def _create_cross_section_reference_tab(self, themes_data: Dict[str, Any]):
        """Create a reference tab showing cross-section themes and their locations"""
        worksheet = self.workbook.add_worksheet('🔄 Cross-Section Themes')
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 20)  # Primary Section
        worksheet.set_column('D:D', 30)  # All Sections
        worksheet.set_column('E:E', 40)  # Cross-Reference Notes
        worksheet.set_column('F:F', 25)  # Processing Status
        
        # Title and instructions
        worksheet.merge_range('A1:F1', "🔄 Cross-Section Themes Reference", self.formats['title'])
        worksheet.merge_range('A2:F2', "IMPORTANT: These themes appear in multiple sections. Process them ONCE in their primary section, then reference here.", self.formats['subheader'])
        
        # Instructions
        worksheet.merge_range('A3:F3', "📋 WORKFLOW: 1) Process theme in Primary Section 2) Mark as 'Processed' here 3) Reference in other sections without re-processing", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Primary Section", "All Sections", 
            "Cross-Reference Notes", "Processing Status"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, self.formats['header'])
        
        # Get cross-section themes
        cross_section_map = self._identify_cross_section_themes(themes_data['themes'])
        
        row = 5
        for theme in themes_data['themes']:
            theme_id = theme.get('theme_id', 'unknown')
            
            if theme_id in cross_section_map:
                sections = cross_section_map[theme_id]
                primary_section = self._get_primary_section_for_theme(theme, cross_section_map)
                
                # Theme ID
                worksheet.write(row, 0, theme_id, self.formats['data_cell'])
                
                # Theme Statement
                worksheet.write(row, 1, theme.get('theme_statement', 'No statement'), self.formats['data_cell'])
                
                # Primary Section
                worksheet.write(row, 2, primary_section.title(), self.formats['data_cell'])
                
                # All Sections
                all_sections = ', '.join([s.title() for s in sections])
                worksheet.write(row, 3, all_sections, self.formats['data_cell'])
                
                # Cross-Reference Notes
                worksheet.write(row, 4, f"Process in {primary_section.title()} section, then reference in: {', '.join([s.title() for s in sections if s != primary_section])}", self.formats['data_cell'])
                
                # Processing Status dropdown
                worksheet.data_validation(row, 5, row, 5, {
                    'validate': 'list',
                    'source': ['PENDING - Not yet processed', 'PROCESSED - Complete in primary section', 'REFERENCED - Added to other sections']
                })
                worksheet.write(row, 5, "PENDING - Not yet processed", self.formats['decision_cell'])
                
                row += 1
        
        # Add summary
        if cross_section_map:
            worksheet.write(row, 0, f"SUMMARY: {len(cross_section_map)} cross-section themes identified", self.formats['header'])
            worksheet.write(row, 1, "Efficiency gain: Process once, reference multiple times", self.formats['data_cell'])
        else:
            worksheet.write(row, 0, "No cross-section themes found", self.formats['data_cell'])

    def _create_pricing_analysis_tab(self, themes_data: Dict[str, Any]):
        """Pricing Analysis Section - Cost-benefit analysis and competitive pricing insights"""
        worksheet = self.workbook.add_worksheet('Pricing Analysis')
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 20)  # Pricing Category
        worksheet.set_column('D:D', 30)  # Cost Impact
        worksheet.set_column('E:E', 60)  # Verbatim Question (DB)
        worksheet.set_column('F:F', 40)  # Quote Text
        worksheet.set_column('G:G', 15)  # Company
        worksheet.set_column('H:H', 15)  # Interviewee
        worksheet.set_column('I:I', 12)  # Sentiment
        worksheet.set_column('J:J', 12)  # Impact Score
        worksheet.set_column('K:K', 25)  # Competitive Context
        worksheet.set_column('L:L', 25)  # Pricing Decision
        worksheet.set_column('M:M', 40)  # Analyst Notes
        
        # Title and instructions
        worksheet.merge_range('A1:M1', "Pricing Analysis Section", self.formats['title'])
        worksheet.merge_range('A2:M2', "PURPOSE: Analyze pricing perceptions, competitive positioning, and cost-benefit insights from customer feedback.", self.formats['subheader'])
        
        # Section context
        worksheet.merge_range('A3:M3', "📖 SECTION CONTEXT: This section focuses on pricing perceptions, competitive cost analysis, value proposition, ROI considerations that influence purchase decisions.", self.formats['data_cell'])
        
        # Research question context
        worksheet.merge_range('A4:M4', "🔍 RESEARCH FOCUS: 'How do customers perceive pricing relative to competitors?' 'What drives value perception?' 'What pricing factors influence purchase decisions?'", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Theme ID", "Theme Statement", "Pricing Category", "Cost Impact", 
            "Verbatim Question (DB)", "Quote Text", "Company", "Interviewee", "Sentiment", "Impact Score", "Competitive Context", "Pricing Decision", "Analyst Notes", "Theme Origin"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, self.formats['header'])
        
        # Process pricing-related themes
        row = 6
        pricing_themes = self._filter_themes_by_pricing_focus(themes_data['themes'])
        
        # Get cross-section map to avoid duplication
        cross_section_map = self._identify_cross_section_themes(themes_data['themes'])
        
        # Filter to only include themes where this is their primary section OR they're not cross-section
        primary_pricing_themes = []
        for theme in pricing_themes:
            theme_id = theme.get('theme_id', 'unknown')
            primary_section = self._get_primary_section_for_theme(theme, cross_section_map)
            
            if primary_section == 'pricing' or theme_id not in cross_section_map:
                primary_pricing_themes.append(theme)
        
        for theme in primary_pricing_themes:
            all_quotes = theme.get('all_quotes', [])
            theme_id = theme.get('theme_id', 'unknown')
            
            # Check if this is a cross-section theme
            is_cross_section = theme_id in cross_section_map
            cross_sections = cross_section_map.get(theme_id, [])
            
            # Write theme info for first quote only
            first_quote = True
            
            for quote in all_quotes:
                # Theme ID (only show for first quote of each theme)
                if first_quote:
                    worksheet.write(row, 0, theme['theme_id'], self.formats['data_cell'])
                    
                    # Add cross-reference info to theme statement if it's a cross-section theme
                    theme_statement = theme.get('theme_statement', 'No statement generated')
                    if is_cross_section:
                        other_sections = [s for s in cross_sections if s != 'pricing']
                        theme_statement += f" [CROSS-SECTION: Also appears in {', '.join(other_sections).title()}]"
                    
                    worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
                    worksheet.write(row, 2, self._categorize_pricing_theme(theme), self.formats['data_cell'])
                    worksheet.write(row, 3, self._assess_cost_impact(theme), self.formats['data_cell'])
                    worksheet.write(row, 4, quote.get('question', ''), self.formats['data_cell'])
                    worksheet.write(row, 5, quote.get('verbatim_response', 'No quote text'), self.formats['data_cell'])
                    worksheet.write(row, 6, quote.get('company', quote.get('company_name', 'Unknown')), self.formats['data_cell'])
                    worksheet.write(row, 7, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                    worksheet.write(row, 8, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                    worksheet.write(row, 9, quote.get('impact_score', 0), self.formats['number'])
                    
                    # Competitive Context
                    competitive_context = self._extract_competitive_context(quote)
                    worksheet.write(row, 10, competitive_context, self.formats['data_cell'])
                    
                    # Pricing Decision dropdown
                    worksheet.data_validation(row, 11, row, 11, {
                        'validate': 'list',
                        'source': ['COMPETITIVE - Matches market', 'PREMIUM - Higher than competitors', 'DISCOUNT - Lower than competitors', 'VALUE - Good ROI', 'EXPENSIVE - Cost barrier', 'UNCLEAR - Pricing not clear']
                    })
                    worksheet.write(row, 11, "", self.formats['decision_cell'])
                    
                    # Analyst Notes
                    worksheet.write(row, 12, "", self.formats['notes_cell'])
                    
                    # Theme Origin column (first quote row only)
                    worksheet.write(row, 13, theme.get('theme_origin', 'discovered').title(), self.formats['data_cell'])
                    
                    row += 1
                
                # Individual quote data (shifted by +1 from previous layout)
                worksheet.write(row, 0, "", self.formats['data_cell'])
                worksheet.write(row, 1, "", self.formats['data_cell'])
                worksheet.write(row, 2, "", self.formats['data_cell'])
                worksheet.write(row, 3, "", self.formats['data_cell'])
                worksheet.write(row, 4, "", self.formats['data_cell'])
                worksheet.write(row, 5, "", self.formats['data_cell'])
                worksheet.write(row, 6, "", self.formats['data_cell'])
                worksheet.write(row, 7, "", self.formats['data_cell'])
                worksheet.write(row, 8, "", self.formats['data_cell'])
                worksheet.write(row, 9, "", self.formats['data_cell'])
                worksheet.write(row, 10, "", self.formats['data_cell'])
                worksheet.write(row, 11, "", self.formats['data_cell'])
                worksheet.write(row, 12, "", self.formats['data_cell'])
                worksheet.write(row, 13, "", self.formats['data_cell'])
                
                row += 1
            
            # Add Theme Decision Row after all quotes for this theme
            worksheet.write(row, 0, f"THEME DECISION: {theme['theme_id']}", self.formats['header'])
            worksheet.write(row, 1, "After reviewing all pricing quotes above, make theme decision:", self.formats['subheader'])
            
            # Theme Decision dropdown
            worksheet.data_validation(row, 11, row, 11, {
                'validate': 'list',
                'source': ['VALIDATED - Use in pricing strategy', 'REJECTED - Insufficient evidence', 'REVISED - Needs statement changes', 'MERGE - Combine with other theme']
            })
            worksheet.write(row, 11, "", self.formats['decision_cell'])
            
            # Theme-level analyst notes
            worksheet.write(row, 12, "", self.formats['notes_cell'])
            
            row += 2
        
        # Add section summary
        row += 2
        worksheet.write(row, 0, "PRICING ANALYSIS SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Pricing Themes: {len(primary_pricing_themes)}")
        worksheet.write(row, 3, "Validated Themes: [Count after review]")
        worksheet.write(row, 6, "Featured Quotes: [Count]")

    def _filter_themes_by_pricing_focus(self, themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter themes that are relevant to pricing analysis"""
        pricing_themes = []
        
        pricing_keywords = [
            'price', 'cost', 'expensive', 'cheap', 'affordable', 'value', 'roi', 'budget',
            'competitive', 'premium', 'discount', 'pricing', 'billing', 'payment',
            'worth', 'investment', 'return', 'savings', 'expense', 'cost-effective',
            'money', 'dollar', 'paid', 'pay', 'charge', 'fee', 'rate', 'costly',
            'economical', 'financial', 'monetary', 'economic', 'fiscal', 'subscription',
            'per case', 'per user', 'flat rate', 'monthly', 'annual', 'credit'
        ]
        
        for theme in themes:
            theme_statement = theme.get('theme_statement', '').lower()
            subject = theme.get('harmonized_subject', '').lower()
            
            # Check if theme contains pricing-related keywords
            has_pricing_keywords = any(keyword in theme_statement for keyword in pricing_keywords)
            is_pricing_subject = 'pricing' in subject or 'commercial' in subject
            
            # Also check quotes for pricing content with product context
            quotes = theme.get('all_quotes', [])
            has_pricing_quotes = False
            for quote in quotes:
                quote_text = quote.get('verbatim_response', '').lower()
                # Look for pricing keywords AND product/service context
                has_pricing = any(keyword in quote_text for keyword in pricing_keywords)
                has_product_context = any(word in quote_text for word in ['product', 'service', 'solution', 'feature', 'capability', 'tool', 'platform', 'software'])
                
                if has_pricing and has_product_context:
                    has_pricing_quotes = True
                    break
                elif has_pricing:  # Still include if just pricing mentioned
                    has_pricing_quotes = True
                    break
            
            # Include if any criteria match
            if has_pricing_keywords or is_pricing_subject or has_pricing_quotes:
                pricing_themes.append(theme)
        
        return pricing_themes

    def _categorize_pricing_theme(self, theme: Dict[str, Any]) -> str:
        """Categorize pricing theme based on content"""
        theme_statement = theme.get('theme_statement', '').lower()
        
        if any(word in theme_statement for word in ['competitive', 'market', 'competitor']):
            return "Competitive Pricing"
        elif any(word in theme_statement for word in ['expensive', 'cost', 'price']):
            return "Cost Perception"
        elif any(word in theme_statement for word in ['value', 'roi', 'worth']):
            return "Value Proposition"
        elif any(word in theme_statement for word in ['billing', 'payment', 'pricing']):
            return "Pricing Model"
        else:
            return "General Pricing"

    def _assess_cost_impact(self, theme: Dict[str, Any]) -> str:
        """Assess the cost impact of a pricing theme"""
        theme_statement = theme.get('theme_statement', '').lower()
        sentiment = theme.get('theme_type', '').lower()
        
        if sentiment == 'strength':
            return "Positive ROI"
        elif sentiment == 'weakness':
            return "Cost Barrier"
        elif 'competitive' in theme_statement:
            return "Market Competitive"
        elif 'value' in theme_statement:
            return "Good Value"
        else:
            return "Neutral"

    def _extract_competitive_context(self, quote: Dict[str, Any]) -> str:
        """Extract competitive context from quote"""
        quote_text = quote.get('verbatim_response', '').lower()
        
        competitors = ['eve', 'evenup', 'parrot', 'filevine']
        found_competitors = [comp for comp in competitors if comp in quote_text]
        
        if found_competitors:
            return f"Competitor: {', '.join(found_competitors).title()}"
        elif 'competitor' in quote_text or 'competition' in quote_text:
            return "Competitive Reference"
        elif 'price' in quote_text or 'cost' in quote_text:
            return "Pricing Focus"
        else:
            return "General Context"

    def _create_company_case_studies_tab(self, themes_data: Dict[str, Any]):
        """Company Case Studies Section - Specific customer success/failure stories with detailed context"""
        worksheet = self.workbook.add_worksheet('Company Case Studies')
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Company Name
        worksheet.set_column('B:B', 20)  # Case Type
        worksheet.set_column('C:C', 30)  # Situation Context
        worksheet.set_column('D:D', 40)  # Key Challenge
        worksheet.set_column('E:E', 40)  # Supio Solution
        worksheet.set_column('F:F', 30)  # Outcome/Impact
        worksheet.set_column('G:G', 60)  # Supporting Quote
        worksheet.set_column('H:H', 15)  # Interviewee
        worksheet.set_column('I:I', 12)  # Sentiment
        worksheet.set_column('J:J', 12)  # Impact Score
        worksheet.set_column('K:K', 25)  # Lessons Learned
        worksheet.set_column('L:L', 40)  # Analyst Notes
        
        # Title and instructions
        worksheet.merge_range('A1:L1', "Company Case Studies Section", self.formats['title'])
        worksheet.merge_range('A2:L2', "PURPOSE: Detailed customer success/failure stories with context, challenges, solutions, and outcomes.", self.formats['subheader'])
        
        # Section context
        worksheet.merge_range('A3:L3', "📖 SECTION CONTEXT: This section provides detailed case studies of specific companies, their challenges, how Supio addressed their needs, and the outcomes achieved.", self.formats['data_cell'])
        
        # Research question context
        worksheet.merge_range('A4:L4', "🔍 RESEARCH FOCUS: 'What specific customer stories demonstrate our value?' 'What challenges did customers face?' 'How did Supio solve their problems?'", self.formats['data_cell'])
        
        # Headers
        headers = [
            "Company Name", "Case Type", "Situation Context", "Key Challenge", 
            "Supio Solution", "Outcome/Impact", "Supporting Quote", "Interviewee", "Sentiment", "Impact Score", "Lessons Learned", "Analyst Notes", "Theme Origin"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, self.formats['header'])
        
        # Process company case studies
        row = 6
        case_studies = self._extract_company_case_studies(themes_data['themes'])
        
        for case in case_studies:
            # Company info
            worksheet.write(row, 0, case['company'], self.formats['data_cell'])
            worksheet.write(row, 1, case['case_type'], self.formats['data_cell'])
            worksheet.write(row, 2, case['situation_context'], self.formats['data_cell'])
            worksheet.write(row, 3, case['key_challenge'], self.formats['data_cell'])
            worksheet.write(row, 4, case['supio_solution'], self.formats['data_cell'])
            worksheet.write(row, 5, case['outcome_impact'], self.formats['data_cell'])
            
            # Supporting quote
            worksheet.write(row, 6, case['supporting_quote'], self.formats['data_cell'])
            worksheet.write(row, 7, case['interviewee'], self.formats['data_cell'])
            worksheet.write(row, 8, case['sentiment'].title(), self.formats['data_cell'])
            worksheet.write(row, 9, case['impact_score'], self.formats['number'])
            
            # Lessons learned dropdown
            worksheet.data_validation(row, 10, row, 10, {
                'validate': 'list',
                'source': ['SUCCESS - Replicable approach', 'CHALLENGE - Address in future', 'OPPORTUNITY - Expand solution', 'INSIGHT - New market understanding', 'PROCESS - Improve workflow']
            })
            worksheet.write(row, 10, "", self.formats['decision_cell'])
            
            # Analyst Notes
            worksheet.write(row, 11, "", self.formats['notes_cell'])
            
            # Theme Origin column (first quote row only)
            worksheet.write(row, 12, theme.get('theme_origin', 'discovered').title(), self.formats['data_cell'])
            
            row += 1
        
        # Add section summary
        row += 2
        worksheet.write(row, 0, "COMPANY CASE STUDIES SUMMARY:", self.formats['header'])
        row += 1
        worksheet.write(row, 0, f"Total Case Studies: {len(case_studies)}")
        worksheet.write(row, 3, "Success Stories: [Count]")
        worksheet.write(row, 6, "Challenges: [Count]")

    def _extract_company_case_studies(self, themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract company case studies from themes"""
        case_studies = []
        companies_processed = set()
        
        for theme in themes:
            quotes = theme.get('all_quotes', [])
            
            for quote in quotes:
                company = quote.get('company', quote.get('company_name', 'Unknown'))
                
                # Skip if we've already processed this company
                if company in companies_processed or company == 'Unknown':
                    continue
                
                # Create case study
                case_study = {
                    'company': company,
                    'case_type': self._determine_case_type(quote, theme),
                    'situation_context': self._extract_situation_context(quote),
                    'key_challenge': self._extract_key_challenge(quote, theme),
                    'supio_solution': self._extract_supio_solution(quote, theme),
                    'outcome_impact': self._extract_outcome_impact(quote, theme),
                    'supporting_quote': quote.get('verbatim_response', 'No quote text'),
                    'interviewee': quote.get('interviewee_name', 'Unknown'),
                    'sentiment': quote.get('sentiment', 'unknown'),
                    'impact_score': quote.get('impact_score', 0),
                    'theme_origin': theme.get('theme_origin', 'discovered'),
                    'research_primary_question': theme.get('research_primary_question', ''),
                    'research_alignment_score': theme.get('research_alignment_score', 0.0)
                }
                
                case_studies.append(case_study)
                companies_processed.add(company)
                
                # Limit to top 3 case studies per company
                if len([c for c in case_studies if c['company'] == company]) >= 3:
                    continue
        
        return case_studies

    def _determine_case_type(self, quote: Dict, theme: Dict) -> str:
        """Determine the type of case study"""
        sentiment = quote.get('sentiment', 'unknown').lower()
        theme_type = theme.get('theme_type', '').lower()
        
        if sentiment == 'positive' or theme_type == 'strength':
            return "Success Story"
        elif sentiment == 'negative' or theme_type == 'weakness':
            return "Challenge Case"
        elif 'opportunity' in theme_type:
            return "Opportunity Case"
        else:
            return "General Case"

    def _extract_situation_context(self, quote: Dict) -> str:
        """Extract situation context from quote"""
        quote_text = quote.get('verbatim_response', '').lower()
        
        # Look for context indicators
        context_keywords = ['when', 'because', 'since', 'after', 'during', 'while']
        for keyword in context_keywords:
            if keyword in quote_text:
                # Extract context around keyword
                start = quote_text.find(keyword)
                end = min(start + 100, len(quote_text))
                context = quote_text[start:end].strip()
                return context.title()
        
        return "Standard evaluation process"

    def _extract_key_challenge(self, quote: Dict, theme: Dict) -> str:
        """Extract key challenge from quote and theme"""
        theme_statement = theme.get('theme_statement', '')
        quote_text = quote.get('verbatim_response', '')
        
        # Look for challenge indicators
        challenge_keywords = ['problem', 'issue', 'challenge', 'difficulty', 'struggle', 'pain']
        for keyword in challenge_keywords:
            if keyword in quote_text.lower():
                # Extract challenge around keyword
                start = quote_text.lower().find(keyword)
                end = min(start + 80, len(quote_text))
                challenge = quote_text[start:end].strip()
                return challenge.title()
        
        # Fallback to theme statement
        if 'struggle' in theme_statement.lower() or 'challenge' in theme_statement.lower():
            return theme_statement
        else:
            return "Process optimization"

    def _extract_supio_solution(self, quote: Dict, theme: Dict) -> str:
        """Extract Supio solution from quote and theme"""
        quote_text = quote.get('verbatim_response', '').lower()
        theme_statement = theme.get('theme_statement', '')
        
        # Look for solution indicators
        solution_keywords = ['supio', 'solution', 'helped', 'provided', 'offered', 'enabled']
        for keyword in solution_keywords:
            if keyword in quote_text:
                # Extract solution around keyword
                start = quote_text.find(keyword)
                end = min(start + 80, len(quote_text))
                solution = quote_text[start:end].strip()
                return solution.title()
        
        # Fallback to theme statement
        if 'supio' in theme_statement.lower():
            return theme_statement
        else:
            return "AI-powered document processing"

    def _extract_outcome_impact(self, quote: Dict, theme: Dict) -> str:
        """Extract outcome and impact from quote and theme"""
        quote_text = quote.get('verbatim_response', '').lower()
        theme_statement = theme.get('theme_statement', '')
        
        # Look for outcome indicators
        outcome_keywords = ['result', 'outcome', 'impact', 'improved', 'saved', 'reduced', 'increased']
        for keyword in outcome_keywords:
            if keyword in quote_text:
                # Extract outcome around keyword
                start = quote_text.find(keyword)
                end = min(start + 80, len(quote_text))
                outcome = quote_text[start:end].strip()
                return outcome.title()
        
        # Fallback based on sentiment
        sentiment = quote.get('sentiment', 'unknown').lower()
        if sentiment == 'positive':
            return "Improved efficiency and time savings"
        elif sentiment == 'negative':
            return "Addressing implementation challenges"
        else:
            return "Ongoing evaluation"

    def _create_report_outline_generator_tab(self, themes_data: Dict[str, Any]):
        """Create enhanced report outline generator based on validated themes"""
        worksheet = self.workbook.add_worksheet('Report Outline Generator')
        
        # Set column widths
        worksheet.set_column('A:A', 30)  # Section
        worksheet.set_column('B:B', 60)  # Content
        worksheet.set_column('C:C', 20)  # Word Count
        worksheet.set_column('D:D', 25)  # Status
        worksheet.set_column('E:E', 40)  # Notes
        
        # Title and instructions
        worksheet.merge_range('A1:E1', "📋 REPORT OUTLINE GENERATOR", self.formats['title'])
        worksheet.merge_range('A2:E2', "Generate design-ready report structure from validated themes", self.formats['subheader'])
        
        row = 4
        
        # Instructions
        worksheet.write(row, 0, "📝 INSTRUCTIONS:", self.formats['header'])
        worksheet.merge_range(f'A{row}:E{row}', "WORKFLOW: 1. Mark themes as 'VALIDATED' in section tabs 2. Note your decisions 3. Regenerate workbook to see changes", self.formats['data_cell'])
        row += 1
        
        # Add detailed workflow instructions
        worksheet.write(row, 0, "🔄 VALIDATION WORKFLOW:", self.formats['subheader'])
        worksheet.merge_range(f'A{row}:E{row}', "This workbook shows simulated validation. To see your actual decisions:", self.formats['data_cell'])
        row += 1
        
        workflow_steps = [
            "1. Go to section tabs (Win Drivers, Loss Factors, etc.)",
            "2. Mark themes as 'VALIDATED - Include in Report' in dropdowns", 
            "3. Note which themes you validated and their quality scores",
            "4. Regenerate workbook with: python generate_excel_workbook.py --client Supio",
            "5. Check this tab again to see your validated themes"
        ]
        
        for step in workflow_steps:
            worksheet.write(row, 0, step, self.formats['data_cell'])
            row += 1
        
        row += 1
        
        # Executive Summary Section
        worksheet.write(row, 0, "📊 EXECUTIVE SUMMARY", self.formats['header'])
        worksheet.write(row, 1, "Key insights and strategic implications", self.formats['data_cell'])
        worksheet.write(row, 2, "2 pages", self.formats['data_cell'])
        worksheet.write(row, 3, "AUTO-GENERATED", self.formats['validated'])
        worksheet.write(row, 4, "Based on validated themes and featured quotes", self.formats['data_cell'])
        row += 1
        
        # Executive Summary Content
        worksheet.write(row, 0, "  • Key Findings")
        worksheet.write(row, 1, "Top 3-5 validated themes with highest impact scores", self.formats['data_cell'])
        worksheet.write(row, 2, "1 page", self.formats['data_cell'])
        worksheet.write(row, 3, "DYNAMIC", self.formats['pending'])
        worksheet.write(row, 4, "Updates based on analyst validation", self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "  • Strategic Implications")
        worksheet.write(row, 1, "Business impact and competitive positioning insights", self.formats['data_cell'])
        worksheet.write(row, 2, "0.5 page", self.formats['data_cell'])
        worksheet.write(row, 3, "DYNAMIC", self.formats['pending'])
        worksheet.write(row, 4, "Based on deal status and competitive analysis", self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "  • Recommendations")
        worksheet.write(row, 1, "Actionable next steps for sales and product teams", self.formats['data_cell'])
        worksheet.write(row, 2, "0.5 page", self.formats['data_cell'])
        worksheet.write(row, 3, "DYNAMIC", self.formats['pending'])
        worksheet.write(row, 4, "Generated from validated themes", self.formats['data_cell'])
        row += 2
        
        # Win Drivers Section
        worksheet.write(row, 0, "🟢 WIN DRIVERS", self.formats['strength'])
        worksheet.write(row, 1, "Validated themes explaining why customers choose you", self.formats['data_cell'])
        worksheet.write(row, 2, "3-4 pages", self.formats['data_cell'])
        worksheet.write(row, 3, "AUTO-GENERATED", self.formats['validated'])
        worksheet.write(row, 4, "Based on validated win driver themes", self.formats['data_cell'])
        row += 1
        
        # Dynamic Win Drivers Content
        validated_win_themes = self._get_validated_themes_by_section(themes_data, 'win_drivers')
        for i, theme in enumerate(validated_win_themes[:5], 1):  # Top 5 themes
            worksheet.write(row, 0, f"  • Theme {i}")
            worksheet.write(row, 1, theme.get('theme_statement', 'No statement')[:100] + "...", self.formats['data_cell'])
            worksheet.write(row, 2, "0.5-1 page", self.formats['data_cell'])
            worksheet.write(row, 3, "VALIDATED", self.formats['validated'])
            worksheet.write(row, 4, f"Quality Score: {theme.get('validation_metrics', {}).get('quality_score', 0):.1f}", self.formats['data_cell'])
            row += 1
        
        if not validated_win_themes:
            worksheet.write(row, 0, "  • No validated themes")
            worksheet.write(row, 1, "Validate themes in 'Win Drivers Section' tab", self.formats['data_cell'])
            worksheet.write(row, 2, "0 pages", self.formats['data_cell'])
            worksheet.write(row, 3, "PENDING", self.formats['pending'])
            worksheet.write(row, 4, "No themes validated yet", self.formats['data_cell'])
            row += 1
        
        row += 2
        
        # Loss Factors Section
        worksheet.write(row, 0, "🔴 LOSS FACTORS", self.formats['weakness'])
        worksheet.write(row, 1, "Validated themes explaining why customers choose competitors", self.formats['data_cell'])
        worksheet.write(row, 2, "2-3 pages", self.formats['data_cell'])
        worksheet.write(row, 3, "AUTO-GENERATED", self.formats['validated'])
        worksheet.write(row, 4, "Based on validated loss factor themes", self.formats['data_cell'])
        row += 1
        
        # Dynamic Loss Factors Content
        validated_loss_themes = self._get_validated_themes_by_section(themes_data, 'loss_factors')
        for i, theme in enumerate(validated_loss_themes[:4], 1):  # Top 4 themes
            worksheet.write(row, 0, f"  • Theme {i}")
            worksheet.write(row, 1, theme.get('theme_statement', 'No statement')[:100] + "...", self.formats['data_cell'])
            worksheet.write(row, 2, "0.5-1 page", self.formats['data_cell'])
            worksheet.write(row, 3, "VALIDATED", self.formats['validated'])
            worksheet.write(row, 4, f"Quality Score: {theme.get('validation_metrics', {}).get('quality_score', 0):.1f}", self.formats['data_cell'])
            row += 1
        
        if not validated_loss_themes:
            worksheet.write(row, 0, "  • No validated themes")
            worksheet.write(row, 1, "Validate themes in 'Loss Factors Section' tab", self.formats['data_cell'])
            worksheet.write(row, 2, "0 pages", self.formats['data_cell'])
            worksheet.write(row, 3, "PENDING", self.formats['pending'])
            worksheet.write(row, 4, "No themes validated yet", self.formats['data_cell'])
            row += 1
        
        row += 2
        
        # Competitive Intelligence Section
        worksheet.write(row, 0, "🟡 COMPETITIVE INTELLIGENCE", self.formats['mixed_signal'])
        worksheet.write(row, 1, "Validated themes about competitive positioning and differentiation", self.formats['data_cell'])
        worksheet.write(row, 2, "2-3 pages", self.formats['data_cell'])
        worksheet.write(row, 3, "AUTO-GENERATED", self.formats['validated'])
        worksheet.write(row, 4, "Based on validated competitive themes", self.formats['data_cell'])
        row += 1
        
        # Dynamic Competitive Intelligence Content
        validated_comp_themes = self._get_validated_themes_by_section(themes_data, 'competitive')
        for i, theme in enumerate(validated_comp_themes[:3], 1):  # Top 3 themes
            worksheet.write(row, 0, f"  • Theme {i}")
            worksheet.write(row, 1, theme.get('theme_statement', 'No statement')[:100] + "...", self.formats['data_cell'])
            worksheet.write(row, 2, "0.5-1 page", self.formats['data_cell'])
            worksheet.write(row, 3, "VALIDATED", self.formats['validated'])
            worksheet.write(row, 4, f"Quality Score: {theme.get('validation_metrics', {}).get('quality_score', 0):.1f}", self.formats['data_cell'])
            row += 1
        
        if not validated_comp_themes:
            worksheet.write(row, 0, "  • No validated themes")
            worksheet.write(row, 1, "Validate themes in 'Competitive Intelligence' tab", self.formats['data_cell'])
            worksheet.write(row, 2, "0 pages", self.formats['data_cell'])
            worksheet.write(row, 3, "PENDING", self.formats['pending'])
            worksheet.write(row, 4, "No themes validated yet", self.formats['data_cell'])
            row += 1
        
        row += 2
        
        # Implementation Insights Section
        worksheet.write(row, 0, "🔧 IMPLEMENTATION INSIGHTS", self.formats['mixed_signal'])
        worksheet.write(row, 1, "Validated themes about implementation process and customer experience", self.formats['data_cell'])
        worksheet.write(row, 2, "1-2 pages", self.formats['data_cell'])
        worksheet.write(row, 3, "AUTO-GENERATED", self.formats['validated'])
        worksheet.write(row, 4, "Based on validated implementation themes", self.formats['data_cell'])
        row += 1
        
        # Dynamic Implementation Insights Content
        validated_impl_themes = self._get_validated_themes_by_section(themes_data, 'implementation')
        for i, theme in enumerate(validated_impl_themes[:2], 1):  # Top 2 themes
            worksheet.write(row, 0, f"  • Theme {i}")
            worksheet.write(row, 1, theme.get('theme_statement', 'No statement')[:100] + "...", self.formats['data_cell'])
            worksheet.write(row, 2, "0.5-1 page", self.formats['data_cell'])
            worksheet.write(row, 3, "VALIDATED", self.formats['validated'])
            worksheet.write(row, 4, f"Quality Score: {theme.get('validation_metrics', {}).get('quality_score', 0):.1f}", self.formats['data_cell'])
            row += 1
        
        if not validated_impl_themes:
            worksheet.write(row, 0, "  • No validated themes")
            worksheet.write(row, 1, "Validate themes in 'Implementation Insights' tab", self.formats['data_cell'])
            worksheet.write(row, 2, "0 pages", self.formats['data_cell'])
            worksheet.write(row, 3, "PENDING", self.formats['pending'])
            worksheet.write(row, 4, "No themes validated yet", self.formats['data_cell'])
            row += 1
        
        row += 2
        
        # Appendices Section
        worksheet.write(row, 0, "📋 APPENDICES", self.formats['header'])
        worksheet.write(row, 1, "Supporting materials and methodology", self.formats['data_cell'])
        worksheet.write(row, 2, "2 pages", self.formats['data_cell'])
        worksheet.write(row, 3, "AUTO-GENERATED", self.formats['validated'])
        worksheet.write(row, 4, "Standard appendices", self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "  • Methodology")
        worksheet.write(row, 1, "Research approach, sample size, and analysis framework", self.formats['data_cell'])
        worksheet.write(row, 2, "0.5 page", self.formats['data_cell'])
        worksheet.write(row, 3, "STATIC", self.formats['data_cell'])
        worksheet.write(row, 4, "Standard methodology section", self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "  • Supporting Evidence")
        worksheet.write(row, 1, "Additional quotes and data tables", self.formats['data_cell'])
        worksheet.write(row, 2, "1 page", self.formats['data_cell'])
        worksheet.write(row, 3, "DYNAMIC", self.formats['pending'])
        worksheet.write(row, 4, "Based on featured quotes", self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "  • Research Questions")
        worksheet.write(row, 1, "Original research questions and coverage analysis", self.formats['data_cell'])
        worksheet.write(row, 2, "0.5 page", self.formats['data_cell'])
        worksheet.write(row, 3, "DYNAMIC", self.formats['pending'])
        worksheet.write(row, 4, "From discussion guide coverage", self.formats['data_cell'])
        row += 2
        
        # Report Summary
        worksheet.write(row, 0, "📊 REPORT SUMMARY", self.formats['header'])
        worksheet.merge_range(f'A{row}:E{row}', "Total report specifications and content overview", self.formats['data_cell'])
        row += 1
        
        # Calculate totals
        total_validated = len(validated_win_themes) + len(validated_loss_themes) + len(validated_comp_themes) + len(validated_impl_themes)
        total_pages = 2 + (len(validated_win_themes) * 0.75) + (len(validated_loss_themes) * 0.75) + (len(validated_comp_themes) * 0.75) + (len(validated_impl_themes) * 0.75) + 2
        
        worksheet.write(row, 0, "  • Total Validated Themes:")
        worksheet.write(row, 1, f"{total_validated} themes across all sections", self.formats['data_cell'])
        worksheet.write(row, 2, f"{total_pages:.1f} pages", self.formats['data_cell'])
        worksheet.write(row, 3, "DYNAMIC", self.formats['pending'])
        worksheet.write(row, 4, "Updates based on analyst validation", self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "  • Featured Quotes:")
        featured_quotes = self._get_featured_quotes_from_validated_themes(themes_data)
        worksheet.write(row, 1, f"{len(featured_quotes)} featured quotes for executive summary", self.formats['data_cell'])
        worksheet.write(row, 2, "1 page", self.formats['data_cell'])
        worksheet.write(row, 3, "DYNAMIC", self.formats['pending'])
        worksheet.write(row, 4, "High-impact quotes for visual treatment", self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "  • Design Elements Needed:")
        design_elements = []
        if validated_win_themes:
            design_elements.append("Win/Loss Ratio Chart")
        if validated_loss_themes:
            design_elements.append("Loss Factor Analysis")
        if validated_comp_themes:
            design_elements.append("Competitive Comparison Matrix")
        if featured_quotes:
            design_elements.append("Quote Callout Boxes")
        
        design_elements_text = ", ".join(design_elements) if design_elements else "None specified yet"
        worksheet.write(row, 1, design_elements_text, self.formats['data_cell'])
        worksheet.write(row, 2, "Variable", self.formats['data_cell'])
        worksheet.write(row, 3, "DYNAMIC", self.formats['pending'])
        worksheet.write(row, 4, "Based on validated content", self.formats['data_cell'])
        row += 2
        
        # Export Instructions
        worksheet.write(row, 0, "📤 EXPORT INSTRUCTIONS", self.formats['header'])
        worksheet.merge_range(f'A{row}:E{row}', "How to use this outline for design team handoff", self.formats['data_cell'])
        row += 1
        
        instructions = [
            "1. Complete theme validation in section tabs",
            "2. Refresh this tab to update outline",
            "3. Copy section content to design brief",
            "4. Include word counts and page specifications",
            "5. Highlight featured quotes for visual treatment"
        ]
        
        for instruction in instructions:
            worksheet.write(row, 0, instruction, self.formats['data_cell'])
            row += 1

    def _create_decision_tracking_tab(self, themes_data: Dict[str, Any]):
        """Create a decision tracking tab for analysts to record their validation decisions"""
        worksheet = self.workbook.add_worksheet('Decision Tracking')
        
        # Set column widths
        worksheet.set_column('A:A', 20)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 20)  # Section
        worksheet.set_column('D:D', 15)  # Quality Score
        worksheet.set_column('E:E', 25)  # Analyst Decision
        worksheet.set_column('F:F', 40)  # Notes
        
        # Title and instructions
        worksheet.merge_range('A1:F1', "📋 ANALYST DECISION TRACKING", self.formats['title'])
        worksheet.merge_range('A2:F2', "Record your validation decisions here, then regenerate workbook to apply them", self.formats['subheader'])
        
        row = 4
        
        # Instructions
        worksheet.write(row, 0, "📝 HOW TO USE:", self.formats['header'])
        worksheet.merge_range(f'A{row}:F{row}', "1. Review themes in section tabs 2. Record decisions here 3. Regenerate workbook", self.formats['data_cell'])
        row += 1
        
        # Headers
        headers = ["Theme ID", "Theme Statement", "Section", "Quality Score", "Decision", "Notes"]
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1
        
        # Add all themes for decision tracking
        all_themes = themes_data['themes']
        for theme in all_themes:
            theme_id = theme.get('theme_id', 'unknown')
            theme_statement = theme.get('theme_statement', 'No statement')[:80] + "..." if len(theme.get('theme_statement', '')) > 80 else theme.get('theme_statement', '')
            section = self._determine_report_section(theme.get('win_loss_category', 'unknown'))
            quality_score = theme.get('validation_metrics', {}).get('quality_score', 0)
            
            worksheet.write(row, 0, theme_id, self.formats['data_cell'])
            worksheet.write(row, 1, theme_statement, self.formats['data_cell'])
            worksheet.write(row, 2, section, self.formats['data_cell'])
            worksheet.write(row, 3, f"{quality_score:.1f}", self.formats['data_cell'])
            
            # Decision dropdown
            worksheet.data_validation(row, 4, row, 4, {
                'validate': 'list',
                'source': ['PENDING', 'VALIDATED', 'REJECTED', 'NEEDS REVISION', 'FEATURED']
            })
            worksheet.write(row, 4, "PENDING", self.formats['pending'])
            
            # Notes cell
            worksheet.write(row, 5, "", self.formats['notes_cell'])
            
            row += 1
        
        # Add summary section
        row += 2
        worksheet.write(row, 0, "📊 DECISION SUMMARY:", self.formats['header'])
        row += 1
        
        # Add formula-based counters
        worksheet.write(row, 0, "Total Themes:")
        total_formula = f'=COUNTA(A6:A{row-3})'
        worksheet.write_formula(row, 1, total_formula, self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Validated Themes:")
        validated_formula = f'=COUNTIF(E6:E{row-2},"VALIDATED")'
        worksheet.write_formula(row, 1, validated_formula, self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Featured Themes:")
        featured_formula = f'=COUNTIF(E6:E{row-2},"FEATURED")'
        worksheet.write_formula(row, 1, featured_formula, self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Rejected Themes:")
        rejected_formula = f'=COUNTIF(E6:E{row-2},"REJECTED")'
        worksheet.write_formula(row, 1, rejected_formula, self.formats['data_cell'])
        row += 2
        
        # Regeneration instructions
        worksheet.write(row, 0, "🔄 TO APPLY DECISIONS:", self.formats['header'])
        worksheet.merge_range(f'A{row}:F{row}', "After recording decisions, regenerate workbook to see them in Report Outline Generator", self.formats['data_cell'])
        row += 1
        
        worksheet.write(row, 0, "Command:")
        worksheet.write(row, 1, "python generate_excel_workbook.py --client Supio --output new_workbook.xlsx", self.formats['data_cell'])
        row += 1

    def _prepare_themes_overview(self, themes: List[Dict[str, Any]]) -> List[Dict]:
        """Prepare the themes overview tab for analysts"""
        overview = []
        
        for theme in themes:
            metrics = theme["validation_metrics"]
            overview.append({
                "Theme ID": theme["theme_id"],
                "Theme Statement": theme["theme_statement"],
                "Theme Type": theme["theme_type"].title(),
                "Harmonized Subject": theme["harmonized_subject"],
                "Theme Origin": theme.get("theme_origin", "discovered").title(),
                "Research Primary Question": theme.get("research_primary_question", ""),
                "Research Alignment %": f"{theme.get('research_alignment_score', 0.0):.1f}",
                "Total Quotes": metrics.get("quotes_count", 0),
                "Companies": metrics.get("companies_count", 0),
                "Avg Impact Score": f"{metrics['avg_impact_score']:.1f}",
                "Quality Score": f"{metrics['quality_score']:.1f}",
                "Competitive Flag": "Yes" if theme.get("competitive_flag", False) else "No",
                "Deal Status Breakdown": self._get_deal_breakdown(theme["all_quotes"]),
                "Sentiment Breakdown": self._get_sentiment_breakdown(theme["all_quotes"])
            })
        
        return overview

    def _create_unified_themes_tab(self, themes_data: Dict[str, Any]):
        """Create a single 'Themes' sheet using the Win Drivers layout, but include all themes."""
        worksheet = self.workbook.add_worksheet('Themes')
        # Reuse the Win Drivers layout columns (already updated to include DB Question before Quote Text)
        # Column widths
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 50)  # Theme Statement
        worksheet.set_column('C:C', 15)  # Theme Origin
        worksheet.set_column('D:D', 20)  # Report Section
        worksheet.set_column('E:E', 30)  # Research Question
        worksheet.set_column('F:F', 40)  # Verbatim Question (DB)
        worksheet.set_column('G:G', 60)  # Quote Text
        worksheet.set_column('H:H', 15)  # Company
        worksheet.set_column('I:I', 15)  # Interviewee
        worksheet.set_column('J:J', 12)  # Sentiment
        worksheet.set_column('K:K', 12)  # Impact Score
        worksheet.set_column('L:L', 15)  # Deal Status
        worksheet.set_column('M:M', 25)  # Quote Classification
        worksheet.set_column('N:N', 25)  # Theme Decision
        worksheet.set_column('O:O', 40)  # Analyst Notes
        
        # Title
        worksheet.merge_range('A1:O1', "Themes - Unified Validation", self.formats['title'])
        worksheet.merge_range('A2:O2', "PURPOSE: Validate all themes with full evidence on a single sheet.", self.formats['subheader'])
        
        headers = [
            "Theme ID", "Theme Statement", "Theme Origin", "Report Section", "Research Question",
            "Verbatim Question (DB)", "Quote Text", "Company", "Interviewee", "Sentiment", "Impact Score", "Deal Status", "Quote Classification", "Theme Decision", "Analyst Notes"
        ]
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, self.formats['header'])
        
        row = 6
        # Inline CSV dropdowns (Numbers-friendly)
        section_csv = '"Win Drivers,Loss Factors,Competitive Intelligence,Implementation Insights,Buyer Profile"'
        decision_csv = '"VALIDATED - Use in report,REJECTED - Insufficient evidence,REVISED - Needs statement changes,MERGE - Combine with other theme,PENDING REVIEW"'
        
        # Initialize themes navigation map
        self.themes_q_first_row = {}
        self.themes_list_by_question = {}
        
        for theme in themes_data['themes']:
            all_quotes = theme.get('all_quotes', [])
            first = True
            for quote in all_quotes:
                if first:
                    worksheet.write(row, 0, theme.get('theme_id', ''), self.formats['data_cell'])
                    worksheet.write(row, 1, theme.get('theme_statement', ''), self.formats['data_cell'])
                    worksheet.write(row, 2, theme.get('theme_origin', 'discovered').title(), self.formats['data_cell'])
                    # Report Section (O11 equivalent on this row)
                    worksheet.data_validation(row, 3, row, 3, {'validate':'list','source': section_csv})
                    worksheet.write(row, 3, "", self.formats['decision_cell'])
                    rq = self._map_theme_to_research_question(theme)
                    worksheet.write(row, 4, rq, self.formats['data_cell'])
                    # Record first theme row per research question for navigation
                    norm_rq = (rq or '').strip().lower()
                    if norm_rq:
                        if norm_rq not in self.themes_q_first_row:
                            self.themes_q_first_row[norm_rq] = row + 1
                        if norm_rq not in self.themes_list_by_question:
                            self.themes_list_by_question[norm_rq] = []
                        self.themes_list_by_question[norm_rq].append(theme)
                    first = False
                else:
                    for c in range(0,5):
                        worksheet.write(row, c, "", self.formats['data_cell'])
                
                # Quote-level fields
                worksheet.write(row, 5, quote.get('question', ''), self.formats['data_cell'])
                worksheet.write(row, 6, quote.get('verbatim_response', 'No quote text'), self.formats['data_cell'])
                worksheet.write(row, 7, quote.get('company', quote.get('company_name', 'Unknown')), self.formats['data_cell'])
                worksheet.write(row, 8, quote.get('interviewee_name', 'Unknown'), self.formats['data_cell'])
                worksheet.write(row, 9, quote.get('sentiment', 'unknown').title(), self.formats['data_cell'])
                worksheet.write(row,10, quote.get('impact_score', 0), self.formats['number'])
                worksheet.write(row,11, quote.get('deal_status', 'UNKNOWN'), self.formats['data_cell'])
                
                # Quote Classification
                worksheet.data_validation(row,12,row,12,{'validate':'list','source':'"FEATURED - Executive summary,PRIMARY - Main evidence,SUPPORTING - Background,EXCLUDE - Do not use"'})
                worksheet.write(row,12, "", self.formats['decision_cell'])
                
                # Theme Decision (N11 equivalent on this row)
                worksheet.data_validation(row,13,row,13,{'validate':'list','source':decision_csv})
                worksheet.write(row,13, "PENDING REVIEW", self.formats['pending'])
                
                # Notes
                worksheet.write(row,14, "", self.formats['notes_cell'])
                row += 1

    def _create_guide_navigator_tab(self, themes_data: Dict[str, Any]):
        """Create Guide Navigator with per-question links to quotes and themes."""
        worksheet = self.workbook.add_worksheet('Guide Navigator')
        worksheet.set_column('A:A', 10)  # QID
        worksheet.set_column('B:B', 70)  # Guide Question (Final)
        worksheet.set_column('C:C', 15)  # Coverage
        worksheet.set_column('D:D', 10)  # Themes
        worksheet.set_column('E:E', 10)  # Quotes
        worksheet.set_column('F:F', 10)  # Companies
        worksheet.set_column('G:G', 20)  # Origin Mix
        worksheet.set_column('H:I', 18)  # Links
        
        worksheet.merge_range('A1:I1', 'Guide Navigator - Work per Question', self.formats['title'])
        worksheet.merge_range('A2:I2', 'Start here: select a question, open quotes or themes to review evidence.', self.formats['subheader'])
        
        headers = ["QID", "Guide Question (Final)", "Coverage", "Themes", "Quotes", "Companies", "Origin Mix", "View Responses", "View Research Themes"]
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, self.formats['header'])
        
        questions = self.discussion_guide or []
        # Build an index for QIDs
        qid_map = {q: f"Q-{i+1:03d}" for i, q in enumerate(questions)}
        row = 5
        
        for q in questions:
            qid = qid_map[q]
            norm_q = (q or '').strip().lower()
            themes_for_q = self.themes_list_by_question.get(norm_q, [])
            themes_count = len(themes_for_q)
            quotes_count = self.raw_data_q_quotes.get(norm_q, 0)
            companies_count = len(self.raw_data_q_companies.get(norm_q, set())) if norm_q in self.raw_data_q_companies else 0
            coverage = "✅ Covered" if themes_count > 0 else ("⚠️ Weak" if quotes_count > 0 else "❌ Uncovered")
            # Origin mix
            origin_mix = {}
            for t in themes_for_q:
                origin = (t.get('theme_origin', 'discovered') or 'discovered').lower()
                origin_mix[origin] = origin_mix.get(origin, 0) + 1
            origin_str = ", ".join([f"{k[:1].upper()}:{v}" for k, v in origin_mix.items()]) if origin_mix else "-"
            
            # Write row
            worksheet.write(row, 0, qid, self.formats['data_cell'])
            worksheet.write(row, 1, q, self.formats['data_cell'])
            worksheet.write(row, 2, coverage, self.formats['data_cell'])
            worksheet.write(row, 3, themes_count, self.formats['number'])
            worksheet.write(row, 4, quotes_count, self.formats['number'])
            worksheet.write(row, 5, companies_count, self.formats['number'])
            worksheet.write(row, 6, origin_str, self.formats['data_cell'])
            
            # Links (only if anchors exist)
            quotes_row = self.question_responses_first_row.get(norm_q)
            if quotes_row:
                # Link to first response row in Question Responses (fallback to Raw Data)
                target_sheet = 'Question Responses' if norm_q in self.question_responses_first_row else '📋 Raw Data'
                worksheet.write_url(row, 7, f"internal:'{target_sheet}'!A{quotes_row}", self.formats['data_cell'], string="Open Responses")
            else:
                worksheet.write(row, 7, "", self.formats['data_cell'])
            theme_row = self.research_themes_first_row.get(norm_q) or self.themes_q_first_row.get(norm_q)
            if theme_row:
                target_sheet = 'Research Themes' if norm_q in self.research_themes_first_row else 'Themes'
                worksheet.write_url(row, 8, f"internal:'{target_sheet}'!A{theme_row}", self.formats['data_cell'], string="Open Research Themes")
            else:
                worksheet.write(row, 8, "", self.formats['data_cell'])
            row += 1

    def _create_question_responses_tab(self, themes_data: Dict[str, Any]):
        """List all responses grouped by discussion guide question with anchors for Navigator."""
        worksheet = self.workbook.add_worksheet('Question Responses')
        worksheet.set_column('A:A', 8)   # QID
        worksheet.set_column('B:B', 70)  # Guide Question (Final)
        worksheet.set_column('C:C', 15)  # Response ID
        worksheet.set_column('D:D', 20)  # Company
        worksheet.set_column('E:E', 15)  # Interviewee
        worksheet.set_column('F:F', 12)  # Sentiment
        worksheet.set_column('G:G', 12)  # Impact
        worksheet.set_column('H:H', 60)  # Verbatim Response
        
        worksheet.merge_range('A1:H1', 'Responses by Discussion Guide Question', self.formats['title'])
        worksheet.merge_range('A2:H2', 'Per-question evidence view to seed Research themes. Follow-ups show a badge and can be promoted to full evidence.', self.formats['subheader'])
        
        headers = ["QID", "Guide Question (Final)", "Response ID", "Company", "Interviewee", "Sentiment", "Impact", "Verbatim Response"]
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, self.formats['header'])
        
        questions = self.discussion_guide or []
        qid_map = {q: f"Q-{i+1:03d}" for i, q in enumerate(questions)}
        # Build a unique quote set across themes
        all_quotes = []
        for t in themes_data['themes']:
            all_quotes.extend(t.get('all_quotes', []))
        seen = set()
        unique_quotes = []
        for q in all_quotes:
            rid = q.get('response_id')
            if rid and rid not in seen:
                unique_quotes.append(q)
                seen.add(rid)
        
        # Group quotes by mapped guide question (fallback to DB question)
        by_q: Dict[str, List[Dict[str, Any]]] = {}
        for q in unique_quotes:
            db_q = (q.get('question', '') or '').strip()
            if not db_q:
                continue
            norm_db = self._normalize(db_q)
            mapped = None
            # Exact normalized match
            if norm_db in getattr(self, '_norm_guide', {}):
                mapped = self._norm_guide[norm_db]
            else:
                # Prefix heuristic (first 6 words) against guide prefixes
                db_prefix = ' '.join(norm_db.split()[:6])
                for gq, gpref in getattr(self, '_guide_prefixes', {}).items():
                    if db_prefix and db_prefix in gpref:
                        mapped = gq
                        break
            key = mapped if mapped else db_q
            # Tag follow-ups if not exact guide question match
            q['__followup_inferred__'] = (mapped is not None and mapped != db_q)
            q['__followup_confidence__'] = float(q.get('mapping_confidence', 0) or 0)
            q['__followup_parent__'] = key if q['__followup_inferred__'] else ''
            by_q.setdefault(key, []).append(q)
        
        row = 5
        self.question_responses_first_row = {}
        # Write guide questions first in order, then any unmapped DB questions
        written_keys = set()
        for qtext in questions:
            qid = qid_map[qtext]
            norm = qtext.strip().lower()
            quotes = by_q.get(qtext, [])
            if quotes:
                self.question_responses_first_row[norm] = row + 1
            for quote in quotes:
                worksheet.write(row, 0, qid, self.formats['data_cell'])
                # Add follow-up badge when inferred
                if quote.get('__followup_inferred__'):
                    badge = f"Follow-up to {qid} (conf {quote.get('__followup_confidence__',0):.2f})"
                    worksheet.write(row, 1, f"{qtext}  —  {badge}", self.formats['data_cell'])
                else:
                    worksheet.write(row, 1, qtext, self.formats['data_cell'])
                worksheet.write(row, 2, quote.get('response_id', ''), self.formats['data_cell'])
                worksheet.write(row, 3, quote.get('company', quote.get('company_name','Unknown')), self.formats['data_cell'])
                worksheet.write(row, 4, quote.get('interviewee_name',''), self.formats['data_cell'])
                worksheet.write(row, 5, str(quote.get('sentiment','unknown')).title(), self.formats['data_cell'])
                worksheet.write(row, 6, quote.get('impact_score', 0), self.formats['number'])
                worksheet.write(row, 7, quote.get('verbatim_response',''), self.formats['data_cell'])
                row += 1
            written_keys.add(qtext)
        # Append unmapped DB question groups so nothing is lost
        for key, quotes in by_q.items():
            if key in written_keys:
                continue
            qid = ''
            norm = self._normalize(key)
            if quotes and norm not in self.question_responses_first_row:
                self.question_responses_first_row[norm] = row + 1
            for quote in quotes:
                worksheet.write(row, 0, qid, self.formats['data_cell'])
                worksheet.write(row, 1, key, self.formats['data_cell'])
                worksheet.write(row, 2, quote.get('response_id', ''), self.formats['data_cell'])
                worksheet.write(row, 3, quote.get('company', quote.get('company_name','Unknown')), self.formats['data_cell'])
                worksheet.write(row, 4, quote.get('interviewee_name',''), self.formats['data_cell'])
                worksheet.write(row, 5, str(quote.get('sentiment','unknown')).title(), self.formats['data_cell'])
                worksheet.write(row, 6, quote.get('impact_score', 0), self.formats['number'])
                worksheet.write(row, 7, quote.get('verbatim_response',''), self.formats['data_cell'])
                row += 1

    def _create_research_themes_tab(self, themes_data: Dict[str, Any]):
        """Show only Research-origin themes (guide-seeded) with anchors per question."""
        worksheet = self.workbook.add_worksheet('Research Themes')
        worksheet.set_column('A:A', 15)  # Theme ID
        worksheet.set_column('B:B', 60)  # Theme Statement
        worksheet.set_column('C:C', 10)  # Origin
        worksheet.set_column('D:D', 10)  # QID
        worksheet.set_column('E:E', 70)  # Guide Question (Final)
        worksheet.set_column('F:F', 12)  # Quality
        worksheet.set_column('G:G', 15)  # Quotes
        worksheet.set_column('H:H', 15)  # Companies
        
        worksheet.merge_range('A1:H1', 'Research Themes (Seeded by Discussion Guide)', self.formats['title'])
        worksheet.merge_range('A2:H2', 'Themes created from question responses; discovered themes are shown separately', self.formats['subheader'])
        
        headers = ["Theme ID", "Theme Statement", "Origin", "QID", "Guide Question (Final)", "Quality Score", "Quotes", "Companies"]
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, self.formats['header'])
        
        questions = self.discussion_guide or []
        qid_map = {q: f"Q-{i+1:03d}" for i, q in enumerate(questions)}
        row = 5
        self.research_themes_first_row = {}
        for t in themes_data['themes']:
            origin = (t.get('theme_origin','discovered') or 'discovered').lower()
            if origin != 'research':
                continue
            rq = t.get('research_primary_question') or t.get('primary_research_question') or ''
            qid = qid_map.get(rq, '')
            if rq:
                norm = rq.strip().lower()
                if norm not in self.research_themes_first_row:
                    self.research_themes_first_row[norm] = row + 1
            vm = t.get('validation_metrics', {})
            worksheet.write(row, 0, t.get('theme_id',''), self.formats['data_cell'])
            worksheet.write(row, 1, t.get('theme_statement',''), self.formats['data_cell'])
            worksheet.write(row, 2, 'Research', self.formats['data_cell'])
            worksheet.write(row, 3, qid, self.formats['data_cell'])
            worksheet.write(row, 4, rq, self.formats['data_cell'])
            worksheet.write(row, 5, f"{vm.get('quality_score',0):.1f}", self.formats['data_cell'])
            worksheet.write(row, 6, vm.get('quotes_count',0), self.formats['number'])
            worksheet.write(row, 7, vm.get('companies_count',0), self.formats['number'])
            # anchor by theme id for linking from roll-up
            tid = t.get('theme_id','')
            if tid:
                self.research_theme_row_by_id[tid] = row + 1
            row += 1
         
    def _create_discovered_themes_tab(self, themes_data: Dict[str, Any]):
        """Show Discovered-origin themes with per-quote evidence context for analyst review."""
        worksheet = self.workbook.add_worksheet('Discovered Themes')
        # Column widths
        worksheet.set_column('A:A', 15)   # Theme ID
        worksheet.set_column('B:B', 90)   # Theme Headline
        # Remove Origin column; shift columns left
        worksheet.set_column('C:C', 20)   # DB Question (Raw)
        worksheet.set_column('D:D', 130)  # Verbatim Quote (wider)
        worksheet.set_column('E:E', 22)   # Company
        worksheet.set_column('F:F', 24)   # Interviewee
        worksheet.set_column('G:G', 12)   # Sentiment
        worksheet.set_column('H:H', 14)   # Deal Status
        worksheet.set_column('I:I', 16)   # Quote Classification

        worksheet.merge_range('A1:I1', 'Discovered Themes (Harmonized Subjects)', self.formats['title'])
        worksheet.merge_range('A2:I2', 'Cross-interview patterns not seeded by the guide. One row per supporting quote.', self.formats['subheader'])

        headers = [
            "Theme ID", "Theme Headline", "DB Question (Raw)", "Verbatim Quote",
            "Company", "Interviewee", "Sentiment", "Deal Status", "Quote Classification"
        ]
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, self.formats['header'])
        
        row = 5
        # Build display IDs for discovered themes
        discovered_display_id_by_tid: Dict[str, str] = {}
        # Assign sequential IDs based on appearance order
        idx_counter = 1
        try:
            worksheet.data_validation(5, 8, 10000, 8, {
                'validate': 'list',
                'source': ['Featured', 'Supporting', 'Exclude']
            })
        except Exception:
            pass
        
        seen_anchor: Dict[str, int] = {}
        # Optional: pull raw data for interviewee/company if not embedded in all_quotes
        try:
            quotes_df = self.db.get_stage1_data_responses(client_id=self.client_id)
        except Exception:
            quotes_df = None
        company_by_id: Dict[str, str] = {}
        interviewee_by_id: Dict[str, str] = {}
        sentiment_by_id: Dict[str, str] = {}
        deal_by_id: Dict[str, str] = {}
        text_by_id: Dict[str, str] = {}
        if quotes_df is not None and not quotes_df.empty:
            for _, r in quotes_df.iterrows():
                rid = r.get('response_id')
                if rid is None:
                    continue
                rid_s = str(rid)
                text_by_id[rid_s] = r.get('verbatim_response', '')
                company_by_id[rid_s] = r.get('company') or r.get('company_name', '')
                interviewee_by_id[rid_s] = r.get('interviewee_name', '')
                sentiment_by_id[rid_s] = r.get('sentiment', '')
                deal_by_id[rid_s] = r.get('deal_status') or r.get('deal_outcome', '')

        for t in themes_data['themes']:
            origin = (t.get('theme_origin','discovered') or 'discovered').lower()
            if origin == 'research':
                continue
            tid = str(t.get('theme_id',''))
            # assign display id if first time seen
            if tid and tid not in discovered_display_id_by_tid:
                discovered_display_id_by_tid[tid] = f"discovered_theme_{idx_counter:03d}"
                idx_counter += 1
            raw_stmt = t.get('theme_statement','')
            quotes = (t.get('all_quotes', []) or [])
            # Compute badges from quotes
            pos = neg = 0
            subjects: Dict[str, int] = {}
            for q in quotes:
                s = (q.get('sentiment') or '').lower()
                if s == 'positive':
                    pos += 1
                elif s == 'negative':
                    neg += 1
                subj = (q.get('harmonized_subject') or q.get('subject') or '').strip()
                if subj:
                    subjects[subj] = subjects.get(subj, 0) + 1
            badge = 'Strength' if pos > neg else ('Weakness' if neg > pos else 'Mixed')
            topic = max(subjects, key=subjects.get) if subjects else 'General'
            # Use taxonomy subject as the standardized name
            headline = topic
            label = f"{topic} [{badge}]"
            if not quotes:
                worksheet.write(row, 0, discovered_display_id_by_tid.get(tid, tid), self.formats['data_cell'])
                worksheet.write(row, 1, label, self.formats['data_cell'])
                worksheet.write(row, 2, '', self.formats['data_cell'])
                worksheet.write(row, 3, '', self.formats['data_cell'])
                worksheet.write(row, 4, '', self.formats['data_cell'])
                worksheet.write(row, 5, '', self.formats['data_cell'])
                worksheet.write(row, 6, '', self.formats['data_cell'])
                worksheet.write(row, 7, '', self.formats['data_cell'])
                worksheet.write(row, 8, '', self.formats['data_cell'])
                if tid and tid not in seen_anchor:
                    self.discovered_theme_row_by_id[tid] = row + 1
                    seen_anchor[tid] = row + 1
                row += 1
                continue

            first_row_for_theme = True
            for q in quotes:
                rid_s = str(q.get('response_id','')) if q.get('response_id') is not None else ''
                vtext = q.get('verbatim_response') or text_by_id.get(rid_s, '')
                company = q.get('company') or q.get('company_name') or company_by_id.get(rid_s, '')
                interviewee = q.get('interviewee_name') or interviewee_by_id.get(rid_s, '')
                sentiment = q.get('sentiment') or sentiment_by_id.get(rid_s, '')
                deal = q.get('deal_status') or q.get('deal_outcome') or deal_by_id.get(rid_s, '')

                worksheet.write(row, 0, (discovered_display_id_by_tid.get(tid, tid) if first_row_for_theme else ''), self.formats['data_cell'])
                worksheet.write(row, 1, label, self.formats['data_cell'])
                worksheet.write(row, 2, q.get('question','') or '', self.formats['data_cell'])
                worksheet.write(row, 3, vtext, self.formats['data_cell'])
                worksheet.write(row, 4, company, self.formats['data_cell'])
                worksheet.write(row, 5, interviewee, self.formats['data_cell'])
                worksheet.write(row, 6, sentiment, self.formats['data_cell'])
                worksheet.write(row, 7, deal, self.formats['data_cell'])
                worksheet.write(row, 8, '', self.formats['data_cell'])

                if tid and tid not in seen_anchor:
                    self.discovered_theme_row_by_id[tid] = row + 1
                    seen_anchor[tid] = row + 1
                first_row_for_theme = False
                row += 1

    def _normalize(self, s: str) -> str:
        return (s or '').strip().lower()
    
    def _build_question_map(self):
        """Map DB question strings to discussion guide questions using normalization and simple fuzzy logic."""
        guide_questions = self.discussion_guide or []
        if not guide_questions:
            self.question_map = {}
            return
        norm_guide = {self._normalize(q): q for q in guide_questions}
        self.question_map = {}
        # Build a small synonym index (first 6 words baseline)
        guide_prefixes = {q: ' '.join(self._normalize(q).split()[:6]) for q in guide_questions}
        # Skip embeddings for fast path
        guide_embs = [None] * len(guide_questions)
        
        # nothing else to do here; mapping occurs on the fly in grouping
        self._norm_guide = norm_guide
        self._guide_prefixes = guide_prefixes
        self._guide_embs = guide_embs
        self._guide_list = guide_questions
    
    def _map_db_question_to_guide(self, db_q: str) -> tuple:
        """Return (mapped_guide_question, method, confidence[0-1])."""
        if not db_q:
            return ("", "None", 0.0)
        norm_db = self._normalize(db_q)
        # mapping-specific cleanup: drop punctuation and digits
        norm_db = ''.join(ch for ch in norm_db if ch.isalnum() or ch.isspace())
        # Exact
        if norm_db in getattr(self, '_norm_guide', {}):
            return (self._norm_guide[norm_db], "Exact", 1.0)
        # Phrase-anchor for Q1: require intro cue + firm-size cue; block if negative/evaluation terms present
        q1_anchors = [
            "introduce yourself",
            "your role",
        ]
        q1_neg_terms = {"evaluate","evaluation","compare","compared","versus","vs","supio","software","criteria","decision","decisions","pricing","price","cost","implementation","features","functionality"}
        has_intro = any(p in norm_db for p in q1_anchors) and ("firm" in norm_db or "attorneys" in norm_db or "support" in norm_db or "size" in norm_db)
        if has_intro and not any(t in norm_db for t in q1_neg_terms):
            # find the first guide question that contains 'introduce' and either 'to start' or equivalent
            for gq in getattr(self, '_guide_list', []):
                gl = gq.lower()
                if ('introduce' in gl) and ('to start' in gl or 'introduce yourself' in gl or 'describe your role' in gl):
                    return (gq, "Anchor", 0.95)
        # Additional hard anchors for common questions to prevent bleed
        # Strengths vs competitors
        if any(k in norm_db for k in ["strength","strengths","weakness","weaknesses"]) and any(k in norm_db for k in ["compare","compared","versus","vs","competitor","competitors"]):
            for gq in getattr(self, '_guide_list', []):
                gl = gq.lower()
                if ('strengths' in gl and 'versus' in gl) or ('strengths' in gl and 'competitor' in gl) or ('weaknesses' in gl and 'versus' in gl):
                    return (gq, "Anchor", 0.95)
        # Pain point importance
        if 'pain point' in norm_db and ('important' in norm_db or 'importance' in norm_db) and ('solve' in norm_db or 'address' in norm_db):
            for gq in getattr(self, '_guide_list', []):
                gl = gq.lower()
                if 'pain point' in gl or ('prompted' in gl and 'evaluate' in gl) or ('problem' in gl and 'solve' in gl):
                    return (gq, "Anchor", 0.9)
        # Experience walkthrough (positive/negative, improve) → implementation/sales experience
        if ('experience' in norm_db or 'walk me through' in norm_db or 'perspective' in norm_db) and (('positive' in norm_db and 'negative' in norm_db) or 'improve' in norm_db):
            for gq in getattr(self, '_guide_list', []):
                gl = gq.lower()
                if ('implementation' in gl and 'process' in gl) or ('sales' in gl and 'experience' in gl):
                    return (gq, "Anchor", 0.9)
        # Prefix heuristic (restrict Q1 overreach by requiring intro terms in prefix for that question)
        db_prefix = ' '.join(norm_db.split()[:6])
        for gq, gpref in getattr(self, '_guide_prefixes', {}).items():
            if db_prefix and db_prefix in gpref:
                # if this looks like Q1 but lacks intro cues, skip prefix mapping
                if ('introduce' in gpref or 'your role' in gpref) and not any(p in norm_db for p in q1_anchors):
                    continue
                return (gq, "Prefix", 0.9)
        # Fuzzy token overlap with stopword removal and discriminative boosts
        stop = {"can","you","your","about","tell","me","walk","through","share","as","was","it","that","how","what","would","to","the","and","or","a","of","for","just","maybe","well","like"}
        db_tokens = {t for t in norm_db.split() if t and t not in stop}
        # Domain anchors for other questions to avoid Q1 bleed
        comp_keywords = {"competitor","competitors","compare","compared","versus","vs","strength","strengths","weakness","weaknesses"}
        pricing_keywords = {"pricing","price","cost","value","expensive","cheap","affordable"}
        impl_keywords = {"implementation","onboarding","setup","deployment","process"}
        eval_keywords = {"criteria","evaluate","assessment","decision","factor","consideration","requirement","vendor","provider","supplier"}
        best_q = None
        best_score = 0.0
        for gq in getattr(self, '_guide_list', []):
            ngq = self._normalize(gq)
            ngq = ''.join(ch for ch in ngq if ch.isalnum() or ch.isspace())
            gtok_all = set(ngq.split())
            gtok = {t for t in gtok_all if t and t not in stop}
            if not gtok:
                continue
            inter = len(db_tokens & gtok)
            union = max(len(db_tokens | gtok), 1)
            score = inter / union
            # boosts based on anchors
            if (db_tokens & comp_keywords) and (gtok_all & comp_keywords):
                score += 0.25
            if (db_tokens & pricing_keywords) and (gtok_all & pricing_keywords):
                score += 0.2
            if (db_tokens & impl_keywords) and (gtok_all & impl_keywords):
                score += 0.2
            if (db_tokens & eval_keywords) and (gtok_all & eval_keywords):
                score += 0.2
            if score > best_score:
                best_score = score
                best_q = gq
        # Question-specific calibration: allow lower threshold for Q1 only when anchors are present; otherwise require high confidence
        q1_cues = {"introduce","yourself","role","firm","size","attorneys","support","staff","share","number"}
        if best_q and (q1_cues & db_tokens) and ("to start" in best_q.lower() or "introduce yourself" in best_q.lower() or "describe your role" in best_q.lower()):
            if has_intro and not any(t in norm_db for t in q1_neg_terms):
                if best_score >= 0.5:
                    return (best_q, "Fuzzy", float(best_score))
            # Without anchors, require stronger score to map to Q1
            if best_score >= 0.8:
                return (best_q, "Fuzzy", float(best_score))
        # General threshold for other questions (relaxed)
        if best_q and best_score >= 0.5:
            return (best_q, "Fuzzy", float(best_score))
        # Nearest/fallback: if we have some overlap, map with low confidence except Q1 without anchors
        if best_q and best_score >= 0.35:
            q1_like = ("introduce" in best_q.lower()) or ("to start" in best_q.lower()) or ("describe your role" in best_q.lower())
            if not q1_like:
                return (best_q, "Fuzzy", float(best_score))
        return ("", "None", 0.0)

    def _create_mapping_qa_tab(self, themes_data: Dict[str, Any]):
        """Create Mapping QA tab showing DB question → Guide question mapping with method and confidence."""
        worksheet = self.workbook.add_worksheet('Mapping QA')
        worksheet.set_column('A:A', 15)  # Response ID
        worksheet.set_column('B:B', 70)  # DB Question
        worksheet.set_column('C:C', 12)  # QID
        worksheet.set_column('D:D', 70)  # Guide Question (Mapped)
        worksheet.set_column('E:E', 14)  # Method
        worksheet.set_column('F:F', 12)  # Confidence
        worksheet.set_column('G:G', 12)  # Manual Override (QID)
        worksheet.set_column('H:H', 12)  # QID (Final)
        
        worksheet.merge_range('A1:H1', 'Mapping QA - DB Question to Guide Question', self.formats['title'])
        worksheet.merge_range('A2:H2', 'Fix low-confidence mappings via Manual Override (QID). Follow-ups can be promoted to full evidence after review.', self.formats['subheader'])
        
        headers = ["Response ID", "DB Question (Raw)", "QID", "Guide Question (Mapped)", "Mapping Method", "Mapping Confidence", "Manual Override (QID)", "QID (Final)"]
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, self.formats['header'])
        
        guide_questions = self.discussion_guide or []
        qid_map = {q: f"Q-{i+1:03d}" for i, q in enumerate(guide_questions)}
        self._build_question_map()
        
        # Unique quotes
        all_quotes = []
        for t in themes_data['themes']:
            all_quotes.extend(t.get('all_quotes', []))
        seen = set()
        unique_quotes = []
        for q in all_quotes:
            rid = q.get('response_id')
            if rid and rid not in seen:
                unique_quotes.append(q)
                seen.add(rid)
        
        row = 5
        for q in unique_quotes:
            rid = q.get('response_id', '')
            db_q = (q.get('question', '') or '').strip()
            mapped_q, method, conf = self._map_db_question_to_guide(db_q)
            mapped_qid = qid_map.get(mapped_q, '')
            worksheet.write(row, 0, rid, self.formats['data_cell'])
            worksheet.write(row, 1, db_q, self.formats['data_cell'])
            worksheet.write(row, 2, mapped_qid, self.formats['data_cell'])
            worksheet.write(row, 3, mapped_q, self.formats['data_cell'])
            worksheet.write(row, 4, method, self.formats['data_cell'])
            worksheet.write(row, 5, f"{conf:.2f}", self.formats['data_cell'])
            worksheet.write(row, 6, "", self.formats['data_cell'])  # Manual override left blank
            worksheet.write(row, 7, mapped_qid, self.formats['data_cell'])  # Final QID (no formula to keep Numbers-friendly)
            row += 1

    def _create_guide_coverage_rollup_tab(self, themes_data: Dict[str, Any]):
        """Create a single roll-up tab: Question → Theme → DB Question (Raw) → Verbatim Quote (+Company, Deal)."""
        worksheet = self.workbook.add_worksheet('Guide Coverage Roll-Up')
        worksheet.set_column('A:A', 70)  # Guide Question (Final)
        worksheet.set_column('B:B', 70)  # DB Question (Raw)
        worksheet.set_column('C:C', 60)  # Theme (Top, per evidence row)
        worksheet.set_column('D:D', 90)  # Verbatim Quote
        worksheet.set_column('E:E', 20)  # Company
        worksheet.set_column('F:F', 14)  # Deal Status
        worksheet.set_column('G:G', 12)  # Evidence Rank
        
        worksheet.merge_range('A1:G1', 'Guide Coverage Roll-Up (Question → Themes → Verbatim Evidence)', self.formats['title'])
        worksheet.merge_range('A2:G2', 'Each row is one quote. Built from Raw Data to guarantee full visibility. Use filters to curate.', self.formats['subheader'])
        
        headers = [
            'Guide Question (Final)', 'DB Question (Raw)', 'Theme (Top 1–N) [Origin]', 'Verbatim Quote', 'Company', 'Deal Status', 'Evidence Rank'
        ]
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, self.formats['header'])
        
        # Build QID index and anchors
        questions = self.discussion_guide or []
        qid_map = {q: f"Q-{i+1:03d}" for i, q in enumerate(questions)}
        self._build_question_map()
        
        # Build response_id -> list of themes map for annotation
        resp_to_themes: Dict[str, List[Tuple[str, str, str]]] = {}
        for t in themes_data['themes']:
            tid = t.get('theme_id','')
            if not tid:
                continue
            origin = (t.get('theme_origin','discovered') or 'discovered').title()
            stmt = t.get('theme_statement','')
            for q in t.get('all_quotes', []) or []:
                rid = q.get('response_id')
                if not rid:
                    continue
                resp_to_themes.setdefault(rid, []).append((tid, origin, stmt))
        
        # Fetch Raw Data to ensure all quotes are included
        try:
            df = self.db.get_stage1_data_responses(client_id=self.client_id)
        except Exception:
            df = None
        raw_quotes: List[Dict[str, Any]] = df.to_dict('records') if df is not None else []
        analyzed_total = len(raw_quotes)
        
        # Group raw quotes by mapped guide question
        by_guide_q: Dict[str, List[Dict[str, Any]]] = {}
        unmapped_quotes: List[Dict[str, Any]] = []
        for rq in raw_quotes:
            db_q = (rq.get('question','') or '').strip()
            mapped_q, method, conf = self._map_db_question_to_guide(db_q)
            if mapped_q:
                by_guide_q.setdefault(mapped_q, []).append(rq)
                rq['__mapping_method__'] = method
                rq['__mapping_confidence__'] = conf
            else:
                unmapped_quotes.append(rq)
                rq['__mapping_method__'] = 'Unmapped'
                rq['__mapping_confidence__'] = 0.0
        
        # Write mapped questions in guide order
        row = 5
        displayed_rows = 0
        displayed_unique_responses: set = set()
        for guide_q in questions:
            quotes = by_guide_q.get(guide_q, [])
            # Rank quotes: unique companies first, then higher impact, then company name
            seen_company_counts: Dict[str, int] = {}
            rank = 1
            for q in sorted(quotes, key=lambda r: (-float(r.get('impact_score',0) or 0), (r.get('company') or r.get('company_name','') or ''))):
                rid = q.get('response_id','')
                company = q.get('company', q.get('company_name','Unknown'))
                seen_company_counts[company] = seen_company_counts.get(company, 0) + 1
                themes_for_resp = resp_to_themes.get(rid, [])
                # If no themes, emit a single row with "No theme yet"
                if not themes_for_resp:
                    theme_label = 'No theme yet'
                    worksheet.write(row, 0, guide_q if rank == 1 else '', self.formats['data_cell'])
                    worksheet.write(row, 1, (q.get('question','') or '').strip() if rank == 1 else '', self.formats['data_cell'])
                    worksheet.write(row, 2, theme_label, self.formats['data_cell'])
                    worksheet.write(row, 3, q.get('verbatim_response',''), self.formats['data_cell'])
                    worksheet.write(row, 4, company, self.formats['data_cell'])
                    worksheet.write(row, 5, q.get('deal_status','') or q.get('deal_outcome',''), self.formats['data_cell'])
                    worksheet.write(row, 6, rank, self.formats['number'])
                    row += 1
                    displayed_rows += 1
                    displayed_unique_responses.add(rid)
                else:
                    # One row per theme the quote supports (Research-only in question views, no links)
                    for (tid, origin, stmt) in themes_for_resp:
                        if str(origin).strip().lower() != 'research':
                            continue
                        theme_text = f"{stmt} [{origin}]" if stmt else f"[{origin}]"
                        worksheet.write(row, 0, guide_q if rank == 1 else '', self.formats['data_cell'])
                        # No hyperlinks in roll-up; show plain text only
                        worksheet.write(row, 1, (q.get('question','') or '').strip() if rank == 1 else '', self.formats['data_cell'])
                        worksheet.write(row, 2, theme_text, self.formats['data_cell'])
                        worksheet.write(row, 3, q.get('verbatim_response',''), self.formats['data_cell'])
                        worksheet.write(row, 4, company, self.formats['data_cell'])
                        worksheet.write(row, 5, q.get('deal_status','') or q.get('deal_outcome',''), self.formats['data_cell'])
                        worksheet.write(row, 6, rank, self.formats['number'])
                        row += 1
                        displayed_rows += 1
                        displayed_unique_responses.add(rid)
                rank += 1
            # Separator
            worksheet.write(row, 0, '', self.formats.get('data_cell'))
            row += 1

        # Unmapped section
        if unmapped_quotes:
            worksheet.merge_range(row, 0, row, 6, 'Unmapped DB Questions (review Mapping QA to fix)', self.formats['subheader'])
            row += 1
            rank = 1
            for q in sorted(unmapped_quotes, key=lambda r: (-float(r.get('impact_score',0) or 0), (r.get('company') or r.get('company_name','') or ''))):
                rid = q.get('response_id','')
                company = q.get('company', q.get('company_name','Unknown'))
                theme_label = 'No theme yet'
                worksheet.write(row, 0, f"{(q.get('question','') or '').strip()} [Unmapped]", self.formats['data_cell'])
                worksheet.write(row, 1, theme_label, self.formats['data_cell'])
                worksheet.write(row, 2, (q.get('question','') or '').strip(), self.formats['data_cell'])
                worksheet.write(row, 3, q.get('verbatim_response',''), self.formats['data_cell'])
                worksheet.write(row, 4, company, self.formats['data_cell'])
                worksheet.write(row, 5, q.get('deal_status','') or q.get('deal_outcome',''), self.formats['data_cell'])
                worksheet.write(row, 6, rank, self.formats['number'])
                row += 1
                displayed_rows += 1
                displayed_unique_responses.add(rid)
                rank += 1
        
        # KPIs box (top-right of header area)
        kpi_row = 3
        kpi_col = 0
        unique_displayed = len(displayed_unique_responses)
        mapped_count = sum(len(v) for v in by_guide_q.values())
        unmapped_count = len(unmapped_quotes)
        worksheet.write(kpi_row, kpi_col, f"Quotes analyzed: {analyzed_total}", self.formats['data_cell'])
        worksheet.write(kpi_row, kpi_col+1, f"Rows displayed: {displayed_rows}", self.formats['data_cell'])
        worksheet.write(kpi_row, kpi_col+2, f"Unique responses displayed: {unique_displayed}", self.formats['data_cell'])
        worksheet.write(kpi_row, kpi_col+3, f"Mapped: {mapped_count}", self.formats['data_cell'])
        worksheet.write(kpi_row, kpi_col+4, f"Unmapped: {unmapped_count}", self.formats['data_cell'])
        
        # Autofilter
        try:
            worksheet.autofilter(4, 0, max(5, row-1), 6)
        except Exception:
            pass
    
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