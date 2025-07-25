#!/usr/bin/env python3
"""
Stage 4 Theme Analyzer - Wrapper for EnhancedThemeGeneratorScalable
Provides a consistent interface for Stage 4 theme generation
"""

import os
import logging
from stage4_theme_generator import EnhancedThemeGeneratorScalable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage4ThemeAnalyzer:
    """Stage 4 Theme Analyzer that wraps EnhancedThemeGeneratorScalable"""
    
    def __init__(self, client_id: str):
        print(f"🔍 DEBUG: Stage4ThemeAnalyzer initialized with client_id={client_id}")
        self.client_id = client_id
        self.generator = EnhancedThemeGeneratorScalable(client_id=client_id)
    
    def process_themes(self, client_id: str = None) -> bool:
        """
        Process themes for the specified client
        
        Args:
            client_id: Client ID to process themes for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if client_id:
                self.client_id = client_id
                self.generator = EnhancedThemeGeneratorScalable(client_id=client_id)
            
            logger.info(f"🎯 Starting Stage 4 theme analysis for client: {self.client_id}")
            
            # Process themes using the enhanced generator
            success = self.generator.process_themes(client_id=self.client_id)
            
            if success:
                logger.info(f"✅ Stage 4 theme analysis completed successfully for {self.client_id}")
                return True
            else:
                logger.error(f"❌ Stage 4 theme analysis failed for {self.client_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in Stage 4 theme analysis: {e}")
            return False
    
    def get_themes_summary(self, client_id: str = None) -> dict:
        """
        Get a summary of themes for the specified client
        
        Args:
            client_id: Client ID to get themes for
            
        Returns:
            dict: Summary of themes
        """
        try:
            if client_id:
                self.client_id = client_id
            
            # Use the generator's database connection to get themes
            themes_data = self.generator.supabase.get_themes(client_id=self.client_id)
            
            if themes_data.empty:
                return {
                    'total_themes': 0,
                    'total_strategic_alerts': 0,
                    'competitive_themes': 0,
                    'companies_covered': 0
                }
            
            # Separate themes and strategic alerts
            themes = themes_data[themes_data['theme_type'] == 'theme']
            strategic_alerts = themes_data[themes_data['theme_type'] == 'strategic_alert']
            
            # Calculate competitive themes
            competitive_themes = len(themes[themes['competitive_flag'] == True])
            
            # Count unique companies
            all_companies = []
            for companies in themes_data['company_ids']:
                if companies and isinstance(companies, str):
                    company_list = [c.strip() for c in companies.split(',') if c.strip()]
                    all_companies.extend(company_list)
            
            companies_covered = len(set(all_companies))
            
            return {
                'total_themes': len(themes),
                'total_strategic_alerts': len(strategic_alerts),
                'competitive_themes': competitive_themes,
                'companies_covered': companies_covered
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting themes summary: {e}")
            return {
                'total_themes': 0,
                'total_strategic_alerts': 0,
                'competitive_themes': 0,
                'companies_covered': 0
            }

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stage 4 Theme Analyzer')
    parser.add_argument('--client_id', type=str, required=True, help='Client ID to process')
    
    args = parser.parse_args()
    
    analyzer = Stage4ThemeAnalyzer(client_id=args.client_id)
    success = analyzer.process_themes()
    
    if success:
        print(f"✅ Stage 4 theme analysis completed successfully for {args.client_id}")
    else:
        print(f"❌ Stage 4 theme analysis failed for {args.client_id}")

if __name__ == "__main__":
    main() 