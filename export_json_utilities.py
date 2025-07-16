#!/usr/bin/env python3
"""
JSON Export Utilities for VOC Pipeline
Provides JSON-to-CSV conversion and other export functions for the JSON refactor
"""

import os
import json
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase_database import SupabaseDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JSONExportUtilities:
    """Utilities for exporting JSON data to various formats"""
    
    def __init__(self, client_id: str = 'default'):
        self.client_id = client_id
        self.db = SupabaseDatabase()
    
    def export_findings_to_csv(self, filters: Optional[Dict] = None) -> str:
        """Export JSON findings to CSV format for business users"""
        try:
            # Get JSON findings
            findings = self.db.get_json_findings(client_id=self.client_id, filters=filters)
            
            if not findings:
                logger.warning("No findings to export")
                return ""
            
            # Convert to DataFrame
            df_data = []
            for finding in findings:
                row = {
                    'finding_id': finding.get('finding_id'),
                    'finding_statement': finding.get('finding_statement'),
                    'finding_category': finding.get('finding_category'),
                    'impact_score': finding.get('impact_score'),
                    'confidence_score': finding.get('confidence_score'),
                    'supporting_quotes': '; '.join(finding.get('supporting_quotes', [])),
                    'companies_mentioned': '; '.join(finding.get('companies_mentioned', [])),
                    'interview_company': finding.get('interview_company'),
                    'interview_date': finding.get('interview_date'),
                    'interview_type': finding.get('interview_type'),
                    'interviewee_name': finding.get('interviewee_name'),
                    'interviewee_role': finding.get('interviewee_role'),
                    'interviewee_company': finding.get('interviewee_company'),
                    'created_at': finding.get('created_at'),
                    'updated_at': finding.get('updated_at')
                }
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"findings_export_{self.client_id}_{timestamp}.csv"
            
            # Export to CSV
            df.to_csv(filename, index=False)
            
            logger.info(f"✅ Exported {len(findings)} findings to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Error exporting findings to CSV: {e}")
            return ""
    
    def export_themes_to_csv(self, filters: Optional[Dict] = None) -> str:
        """Export JSON themes to CSV format for business users"""
        try:
            # Get JSON themes
            themes = self.db.get_json_themes(client_id=self.client_id, filters=filters)
            
            if not themes:
                logger.warning("No themes to export")
                return ""
            
            # Convert to DataFrame
            df_data = []
            for theme in themes:
                row = {
                    'theme_id': theme.get('theme_id'),
                    'theme_name': theme.get('theme_name'),
                    'theme_description': theme.get('theme_description'),
                    'strategic_importance': theme.get('strategic_importance'),
                    'action_items': '; '.join(theme.get('action_items', [])),
                    'related_findings': '; '.join(theme.get('related_findings', [])),
                    'alert_id': theme.get('alert_id'),
                    'alert_type': theme.get('alert_type'),
                    'alert_message': theme.get('alert_message'),
                    'alert_priority': theme.get('alert_priority'),
                    'recommended_actions': '; '.join(theme.get('recommended_actions', [])),
                    'analysis_date': theme.get('analysis_date'),
                    'created_at': theme.get('created_at'),
                    'updated_at': theme.get('updated_at')
                }
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"themes_export_{self.client_id}_{timestamp}.csv"
            
            # Export to CSV
            df.to_csv(filename, index=False)
            
            logger.info(f"✅ Exported {len(themes)} themes to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Error exporting themes to CSV: {e}")
            return ""
    
    def export_comprehensive_report(self, filters: Optional[Dict] = None) -> str:
        """Export comprehensive JSON report with findings and themes"""
        try:
            # Get both findings and themes
            findings = self.db.get_json_findings(client_id=self.client_id, filters=filters)
            themes = self.db.get_json_themes(client_id=self.client_id, filters=filters)
            
            # Create comprehensive report structure
            report = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'client_id': self.client_id,
                    'total_findings': len(findings),
                    'total_themes': len(themes),
                    'filters_applied': filters or {}
                },
                'findings': findings,
                'themes': themes,
                'summary': {
                    'high_impact_findings': len([f for f in findings if f.get('impact_score', 0) > 7.0]),
                    'high_confidence_findings': len([f for f in findings if f.get('confidence_score', 0) > 7.0]),
                    'high_priority_themes': len([t for t in themes if t.get('strategic_importance') == 'HIGH']),
                    'strategic_alerts': len([t for t in themes if t.get('alert_id')])
                }
            }
            
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_report_{self.client_id}_{timestamp}.json"
            
            # Export to JSON
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"✅ Exported comprehensive report to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Error exporting comprehensive report: {e}")
            return ""
    
    def export_executive_summary(self, filters: Optional[Dict] = None) -> str:
        """Export executive summary in JSON format"""
        try:
            # Get findings and themes
            findings = self.db.get_json_findings(client_id=self.client_id, filters=filters)
            themes = self.db.get_json_themes(client_id=self.client_id, filters=filters)
            
            # Create executive summary
            summary = {
                'executive_summary': {
                    'generated_date': datetime.now().isoformat(),
                    'client_id': self.client_id,
                    'key_insights': {
                        'total_findings': len(findings),
                        'total_themes': len(themes),
                        'top_findings': self._get_top_findings(findings, 5),
                        'top_themes': self._get_top_themes(themes, 5),
                        'strategic_alerts': self._get_strategic_alerts(themes)
                    },
                    'recommendations': self._generate_recommendations(findings, themes)
                }
            }
            
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"executive_summary_{self.client_id}_{timestamp}.json"
            
            # Export to JSON
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"✅ Exported executive summary to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Error exporting executive summary: {e}")
            return ""
    
    def _get_top_findings(self, findings: List[Dict], limit: int = 5) -> List[Dict]:
        """Get top findings by impact and confidence scores"""
        sorted_findings = sorted(
            findings,
            key=lambda x: (x.get('impact_score', 0) + x.get('confidence_score', 0)) / 2,
            reverse=True
        )
        
        return [
            {
                'finding_id': f.get('finding_id'),
                'finding_statement': f.get('finding_statement'),
                'impact_score': f.get('impact_score'),
                'confidence_score': f.get('confidence_score'),
                'finding_category': f.get('finding_category')
            }
            for f in sorted_findings[:limit]
        ]
    
    def _get_top_themes(self, themes: List[Dict], limit: int = 5) -> List[Dict]:
        """Get top themes by strategic importance"""
        high_priority = [t for t in themes if t.get('strategic_importance') == 'HIGH']
        medium_priority = [t for t in themes if t.get('strategic_importance') == 'MEDIUM']
        
        # Combine high and medium priority themes
        sorted_themes = high_priority + medium_priority
        
        return [
            {
                'theme_id': t.get('theme_id'),
                'theme_name': t.get('theme_name'),
                'theme_description': t.get('theme_description'),
                'strategic_importance': t.get('strategic_importance'),
                'action_items': t.get('action_items', [])
            }
            for t in sorted_themes[:limit]
        ]
    
    def _get_strategic_alerts(self, themes: List[Dict]) -> List[Dict]:
        """Get strategic alerts from themes"""
        alerts = []
        for theme in themes:
            if theme.get('alert_id'):
                alerts.append({
                    'alert_id': theme.get('alert_id'),
                    'alert_type': theme.get('alert_type'),
                    'alert_message': theme.get('alert_message'),
                    'alert_priority': theme.get('alert_priority'),
                    'recommended_actions': theme.get('recommended_actions', [])
                })
        
        return alerts
    
    def _generate_recommendations(self, findings: List[Dict], themes: List[Dict]) -> List[str]:
        """Generate recommendations based on findings and themes"""
        recommendations = []
        
        # Analyze findings for patterns
        high_impact_findings = [f for f in findings if f.get('impact_score', 0) > 7.0]
        if high_impact_findings:
            recommendations.append(f"Focus on {len(high_impact_findings)} high-impact findings that require immediate attention")
        
        # Analyze themes for action items
        high_priority_themes = [t for t in themes if t.get('strategic_importance') == 'HIGH']
        if high_priority_themes:
            recommendations.append(f"Prioritize {len(high_priority_themes)} high-priority themes for strategic planning")
        
        # Check for strategic alerts
        alerts = [t for t in themes if t.get('alert_id')]
        if alerts:
            recommendations.append(f"Address {len(alerts)} strategic alerts that require urgent attention")
        
        # Generate category-specific recommendations
        categories = {}
        for finding in findings:
            category = finding.get('finding_category', 'Other')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        top_category = max(categories.items(), key=lambda x: x[1]) if categories else None
        if top_category:
            recommendations.append(f"Focus on {top_category[0]} category with {top_category[1]} findings")
        
        return recommendations
    
    def export_to_excel(self, filters: Optional[Dict] = None) -> str:
        """Export findings and themes to Excel with multiple sheets"""
        try:
            # Get data
            findings = self.db.get_json_findings(client_id=self.client_id, filters=filters)
            themes = self.db.get_json_themes(client_id=self.client_id, filters=filters)
            
            # Create Excel writer
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"voc_report_{self.client_id}_{timestamp}.xlsx"
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Findings sheet
                if findings:
                    findings_df = pd.DataFrame([
                        {
                            'finding_id': f.get('finding_id'),
                            'finding_statement': f.get('finding_statement'),
                            'finding_category': f.get('finding_category'),
                            'impact_score': f.get('impact_score'),
                            'confidence_score': f.get('confidence_score'),
                            'companies_mentioned': '; '.join(f.get('companies_mentioned', [])),
                            'interview_company': f.get('interview_company'),
                            'created_at': f.get('created_at')
                        }
                        for f in findings
                    ])
                    findings_df.to_excel(writer, sheet_name='Findings', index=False)
                
                # Themes sheet
                if themes:
                    themes_df = pd.DataFrame([
                        {
                            'theme_id': t.get('theme_id'),
                            'theme_name': t.get('theme_name'),
                            'theme_description': t.get('theme_description'),
                            'strategic_importance': t.get('strategic_importance'),
                            'action_items': '; '.join(t.get('action_items', [])),
                            'alert_id': t.get('alert_id'),
                            'alert_type': t.get('alert_type'),
                            'alert_priority': t.get('alert_priority'),
                            'created_at': t.get('created_at')
                        }
                        for t in themes
                    ])
                    themes_df.to_excel(writer, sheet_name='Themes', index=False)
                
                # Summary sheet
                summary_data = {
                    'Metric': ['Total Findings', 'Total Themes', 'High Impact Findings', 'High Priority Themes', 'Strategic Alerts'],
                    'Count': [
                        len(findings),
                        len(themes),
                        len([f for f in findings if f.get('impact_score', 0) > 7.0]),
                        len([t for t in themes if t.get('strategic_importance') == 'HIGH']),
                        len([t for t in themes if t.get('alert_id')])
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            logger.info(f"✅ Exported to Excel: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Error exporting to Excel: {e}")
            return ""

def run_json_export_examples():
    """Run examples of JSON export utilities"""
    utilities = JSONExportUtilities()
    
    print("📊 JSON Export Utilities Examples:")
    print("=" * 50)
    
    # Export findings to CSV
    csv_file = utilities.export_findings_to_csv()
    if csv_file:
        print(f"✅ Findings CSV: {csv_file}")
    
    # Export themes to CSV
    csv_file = utilities.export_themes_to_csv()
    if csv_file:
        print(f"✅ Themes CSV: {csv_file}")
    
    # Export comprehensive report
    report_file = utilities.export_comprehensive_report()
    if report_file:
        print(f"✅ Comprehensive Report: {report_file}")
    
    # Export executive summary
    summary_file = utilities.export_executive_summary()
    if summary_file:
        print(f"✅ Executive Summary: {summary_file}")
    
    # Export to Excel
    excel_file = utilities.export_to_excel()
    if excel_file:
        print(f"✅ Excel Report: {excel_file}")

if __name__ == "__main__":
    run_json_export_examples() 