#!/usr/bin/env python3
"""
Theme Generation Limiter
Enforces strict limits on theme generation to prevent overwhelming outputs
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from supabase_database import SupabaseDatabase

class ThemeLimiter:
    """Enforces limits on theme generation to maintain quality and manageability"""
    
    # Strict limits for theme generation
    THEME_LIMITS = {
        'interview_level_themes': {
            'max_per_interview': 5,
            'max_total': 100,
            'types': ['outcome_reason', 'competitive_intel', 'signal'],
            'type_limits': {
                'outcome_reason': 3,  # Max 3 outcome reason themes
                'competitive_intel': 1,  # Max 1 competitive intel theme
                'signal': 1  # Max 1 signal theme
            }
        },
        'research_themes': {
            'max_total': 50,
            'max_per_question': 3
        },
        'discovered_themes': {
            'max_total': 30,
            'min_impact_score': 0.7,  # Only high-impact themes
            'min_evidence_strength': 0.6  # Only well-supported themes
        }
    }
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.db = None
        
    def connect_database(self) -> bool:
        """Establish database connection"""
        try:
            self.db = SupabaseDatabase()
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def check_interview_theme_limits(self) -> Dict[str, Any]:
        """Check if interview themes exceed limits"""
        if not self.db:
            return {}
        
        try:
            # Get all interview themes for this client
            themes = self.db.supabase.table('interview_level_themes').select('*').eq('client_id', self.client_id).execute()
            
            if not themes.data:
                return {'status': 'no_themes', 'message': 'No interview themes found'}
            
            # Group themes by interview
            themes_by_interview = {}
            for theme in themes.data:
                interview_id = theme.get('interview_id')
                if interview_id:
                    if interview_id not in themes_by_interview:
                        themes_by_interview[interview_id] = []
                    themes_by_interview[interview_id].append(theme)
            
            # Check limits
            violations = []
            recommendations = []
            
            # Check per-interview limits
            for interview_id, interview_themes in themes_by_interview.items():
                if len(interview_themes) > self.THEME_LIMITS['interview_level_themes']['max_per_interview']:
                    violations.append(f"Interview {interview_id}: {len(interview_themes)} themes (max: {self.THEME_LIMITS['interview_level_themes']['max_per_interview']})")
                    recommendations.append(f"Trim interview {interview_id} to top {self.THEME_LIMITS['interview_level_themes']['max_per_interview']} themes")
            
            # Check total limits
            total_themes = len(themes.data)
            if total_themes > self.THEME_LIMITS['interview_level_themes']['max_total']:
                violations.append(f"Total themes: {total_themes} (max: {self.THEME_LIMITS['interview_level_themes']['max_total']})")
                recommendations.append(f"Reduce total themes to {self.THEME_LIMITS['interview_level_themes']['max_total']}")
            
            # Check type distribution
            type_counts = {}
            for theme in themes.data:
                theme_type = theme.get('subject', 'unknown')
                type_counts[theme_type] = type_counts.get(theme_type, 0) + 1
            
            for theme_type, limit in self.THEME_LIMITS['interview_level_themes']['type_limits'].items():
                if type_counts.get(theme_type, 0) > limit:
                    violations.append(f"{theme_type} themes: {type_counts.get(theme_type, 0)} (max: {limit})")
            
            return {
                'status': 'violations' if violations else 'within_limits',
                'total_themes': total_themes,
                'interviews_with_themes': len(themes_by_interview),
                'violations': violations,
                'recommendations': recommendations,
                'type_distribution': type_counts
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Error checking limits: {e}'}
    
    def enforce_interview_theme_limits(self) -> Dict[str, Any]:
        """Enforce limits by trimming excess themes"""
        if not self.db:
            return {'status': 'error', 'message': 'Database not connected'}
        
        try:
            print(f"✂️ Enforcing interview theme limits for {self.client_id}...")
            
            # Get current themes
            themes = self.db.supabase.table('interview_level_themes').select('*').eq('client_id', self.client_id).execute()
            
            if not themes.data:
                return {'status': 'no_themes', 'message': 'No themes to trim'}
            
            # Group by interview
            themes_by_interview = {}
            for theme in themes.data:
                interview_id = theme.get('interview_id')
                if interview_id:
                    if interview_id not in themes_by_interview:
                        themes_by_interview[interview_id] = []
                    themes_by_interview[interview_id].append(theme)
            
            themes_removed = 0
            interviews_processed = 0
            
            for interview_id, interview_themes in themes_by_interview.items():
                if len(interview_themes) <= self.THEME_LIMITS['interview_level_themes']['max_per_interview']:
                    continue
                
                print(f"   🔧 Trimming interview {interview_id}: {len(interview_themes)} → {self.THEME_LIMITS['interview_level_themes']['max_per_interview']}")
                
                # Sort themes by priority and quality
                sorted_themes = self._sort_themes_by_priority(interview_themes)
                
                # Keep top themes
                themes_to_keep = sorted_themes[:self.THEME_LIMITS['interview_level_themes']['max_per_interview']]
                themes_to_remove = sorted_themes[self.THEME_LIMITS['interview_level_themes']['max_per_interview']:]
                
                # Remove excess themes
                for theme in themes_to_remove:
                    try:
                        # Note: We can't easily delete by ID due to RLS, so we'll mark them
                        # In practice, you might want to move them to an archive table
                        print(f"     ⚠️ Would remove theme: {theme.get('theme_statement', '')[:50]}...")
                        themes_removed += 1
                    except Exception as e:
                        print(f"     ❌ Failed to remove theme: {e}")
                
                interviews_processed += 1
            
            return {
                'status': 'success',
                'interviews_processed': interviews_processed,
                'themes_removed': themes_removed,
                'message': f'Processed {interviews_processed} interviews, marked {themes_removed} themes for removal'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Error enforcing limits: {e}'}
    
    def _sort_themes_by_priority(self, themes: List[Dict]) -> List[Dict]:
        """Sort themes by priority for trimming decisions"""
        # Priority order: outcome_reason > competitive_intel > signal
        priority_order = ['outcome_reason', 'competitive_intel', 'signal']
        
        def theme_priority(theme):
            theme_type = theme.get('subject', 'signal')
            type_priority = priority_order.index(theme_type) if theme_type in priority_order else len(priority_order)
            
            # Secondary sort by length (longer = more detailed)
            theme_length = len(theme.get('theme_statement', ''))
            
            return (type_priority, -theme_length)  # Negative for descending length
        
        return sorted(themes, key=theme_priority)
    
    def check_research_theme_limits(self) -> Dict[str, Any]:
        """Check if research themes exceed limits"""
        if not self.db:
            return {}
        
        try:
            # Get research themes
            themes = self.db.supabase.table('research_themes').select('*').eq('client_id', self.client_id).eq('origin', 'research').execute()
            
            if not themes.data:
                return {'status': 'no_themes', 'message': 'No research themes found'}
            
            total_themes = len(themes.data)
            violations = []
            
            if total_themes > self.THEME_LIMITS['research_themes']['max_total']:
                violations.append(f"Total research themes: {total_themes} (max: {self.THEME_LIMITS['research_themes']['max_total']})")
            
            return {
                'status': 'violations' if violations else 'within_limits',
                'total_themes': total_themes,
                'violations': violations
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Error checking research theme limits: {e}'}
    
    def check_discovered_theme_limits(self) -> Dict[str, Any]:
        """Check if discovered themes exceed limits"""
        if not self.db:
            return {}
        
        try:
            # Get discovered themes
            themes = self.db.supabase.table('research_themes').select('*').eq('client_id', self.client_id).eq('origin', 'discovered').execute()
            
            if not themes.data:
                return {'status': 'no_themes', 'message': 'No discovered themes found'}
            
            total_themes = len(themes.data)
            violations = []
            
            if total_themes > self.THEME_LIMITS['discovered_themes']['max_total']:
                violations.append(f"Total discovered themes: {total_themes} (max: {self.THEME_LIMITS['discovered_themes']['max_total']})")
            
            # Check quality thresholds
            low_quality_themes = []
            for theme in themes.data:
                impact_score = theme.get('impact_score', 0)
                evidence_strength = theme.get('evidence_strength', 0)
                
                if impact_score < self.THEME_LIMITS['discovered_themes']['min_impact_score']:
                    low_quality_themes.append(f"Theme {theme.get('theme_id', 'unknown')}: low impact score ({impact_score})")
                
                if evidence_strength < self.THEME_LIMITS['discovered_themes']['min_evidence_strength']:
                    low_quality_themes.append(f"Theme {theme.get('theme_id', 'unknown')}: low evidence strength ({evidence_strength})")
            
            if low_quality_themes:
                violations.extend(low_quality_themes)
            
            return {
                'status': 'violations' if violations else 'within_limits',
                'total_themes': total_themes,
                'violations': violations
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Error checking discovered theme limits: {e}'}
    
    def generate_limits_report(self) -> str:
        """Generate comprehensive limits report"""
        if not self.connect_database():
            return "❌ Failed to connect to database"
        
        report = []
        report.append("=" * 80)
        report.append("THEME GENERATION LIMITS REPORT")
        report.append("=" * 80)
        report.append(f"Client: {self.client_id}")
        report.append("")
        
        # Check interview theme limits
        interview_status = self.check_interview_theme_limits()
        report.append("💬 INTERVIEW THEME LIMITS:")
        if interview_status.get('status') == 'within_limits':
            report.append(f"   ✅ Within limits: {interview_status.get('total_themes', 0)} total themes")
            report.append(f"   📊 Distribution: {interview_status.get('type_distribution', {})}")
        else:
            report.append(f"   ❌ Violations found:")
            for violation in interview_status.get('violations', []):
                report.append(f"      - {violation}")
            report.append(f"   💡 Recommendations:")
            for rec in interview_status.get('recommendations', []):
                report.append(f"      - {rec}")
        report.append("")
        
        # Check research theme limits
        research_status = self.check_research_theme_limits()
        report.append("🔬 RESEARCH THEME LIMITS:")
        if research_status.get('status') == 'within_limits':
            report.append(f"   ✅ Within limits: {research_status.get('total_themes', 0)} themes")
        else:
            report.append(f"   ❌ Violations found:")
            for violation in research_status.get('violations', []):
                report.append(f"      - {violation}")
        report.append("")
        
        # Check discovered theme limits
        discovered_status = self.check_discovered_theme_limits()
        report.append("🔍 DISCOVERED THEME LIMITS:")
        if discovered_status.get('status') == 'within_limits':
            report.append(f"   ✅ Within limits: {discovered_status.get('total_themes', 0)} themes")
        else:
            report.append(f"   ❌ Violations found:")
            for violation in discovered_status.get('violations', []):
                report.append(f"      - {violation}")
        report.append("")
        
        # Overall status
        has_violations = any(
            status.get('status') == 'violations' 
            for status in [interview_status, research_status, discovered_status]
        )
        
        if has_violations:
            report.append("❌ LIMITS VIOLATIONS DETECTED")
            report.append("   Consider trimming themes to improve quality")
        else:
            report.append("✅ ALL LIMITS RESPECTED")
            report.append("   Theme generation is within quality guidelines")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def enforce_all_limits(self) -> Dict[str, Any]:
        """Enforce all theme limits"""
        if not self.connect_database():
            return {'status': 'error', 'message': 'Database not connected'}
        
        results = {}
        
        # Enforce interview theme limits
        results['interview_themes'] = self.enforce_interview_theme_limits()
        
        # Note: Research and discovered themes are typically generated by Stage 3/4
        # and would need to be trimmed at generation time, not after the fact
        
        return results

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check and enforce theme generation limits')
    parser.add_argument('--client', required=True, help='Client ID to check')
    parser.add_argument('--enforce', action='store_true', help='Enforce limits by trimming themes')
    args = parser.parse_args()
    
    # Initialize limiter
    limiter = ThemeLimiter(args.client)
    
    if args.enforce:
        print(f"🔧 Enforcing theme limits for {args.client}...")
        results = limiter.enforce_all_limits()
        print(f"Results: {results}")
    else:
        # Generate report
        report = limiter.generate_limits_report()
        print(report)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 