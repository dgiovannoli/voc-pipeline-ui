#!/usr/bin/env python3
"""
CSV Validator & Auto-Fixer
Validates CSV uploads and automatically fixes common issues before processing
"""

import os
import sys
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

class CSVValidator:
    """Validates and auto-fixes CSV files for VOC pipeline processing"""
    
    # Standard required columns for VOC pipeline
    REQUIRED_COLUMNS = {
        'Interview Contact Full Name': ['Contact ID', 'Contact Name', 'Interviewee Name', 'Name'],
        'Interview Contact Company Name': ['Company', 'Company Name', 'Organization', 'Firm'],
        'Completion Date': ['Scheduled Date', 'Interview Date', 'Date', 'Meeting Date'],
        'Industry': ['Industry', 'Sector', 'Business Type'],
        'Interview Status': ['Status', 'Interview Status', 'Meeting Status'],
        'Raw Transcript': ['Raw Transcript', 'Transcript', 'Interview Text', 'Full Transcript', 'Notes']
    }
    
    # Common column name variations
    COLUMN_VARIATIONS = {
        'Contact ID': 'Interview Contact Full Name',
        'Contact Name': 'Interview Contact Full Name', 
        'Interviewee Name': 'Interview Contact Full Name',
        'Name': 'Interview Contact Full Name',
        'Company': 'Interview Contact Company Name',
        'Company Name': 'Interview Contact Company Name',
        'Organization': 'Interview Contact Company Name',
        'Firm': 'Interview Contact Company Name',
        'Scheduled Date': 'Completion Date',
        'Interview Date': 'Completion Date',
        'Date': 'Completion Date',
        'Meeting Date': 'Completion Date',
        'Sector': 'Industry',
        'Business Type': 'Industry',
        'Status': 'Interview Status',
        'Meeting Status': 'Interview Status',
        'Transcript': 'Raw Transcript',
        'Interview Text': 'Raw Transcript',
        'Full Transcript': 'Raw Transcript',
        'Notes': 'Raw Transcript'
    }
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
        self.issues = []
        self.fixes_applied = []
        
    def load_csv(self) -> bool:
        """Load CSV file and handle encoding issues"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    self.df = pd.read_csv(self.csv_path, encoding=encoding)
                    print(f"✅ CSV loaded successfully with {encoding} encoding")
                    print(f"   📊 Shape: {self.df.shape}")
                    return True
                except UnicodeDecodeError:
                    continue
            
            print(f"❌ Failed to load CSV with any encoding")
            return False
            
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False
    
    def validate_columns(self) -> Dict[str, List[str]]:
        """Check for required columns and identify missing ones"""
        if self.df is None:
            return {}
        
        current_columns = list(self.df.columns)
        missing_columns = {}
        
        for required_col, variations in self.REQUIRED_COLUMNS.items():
            found = False
            
            # Check if exact column exists
            if required_col in current_columns:
                found = True
                continue
                
            # Check variations
            for variation in variations:
                if variation in current_columns:
                    found = True
                    break
            
            if not found:
                missing_columns[required_col] = variations
        
        return missing_columns
    
    def auto_fix_columns(self) -> bool:
        """Automatically fix column name issues"""
        if self.df is None:
            return False
        
        print(f"🔧 Auto-fixing column names...")
        
        # Rename variations to standard names
        for variation, standard_name in self.COLUMN_VARIATIONS.items():
            if variation in self.df.columns and standard_name not in self.df.columns:
                self.df = self.df.rename(columns={variation: standard_name})
                self.fixes_applied.append(f"Renamed '{variation}' → '{standard_name}'")
                print(f"   ✅ Renamed '{variation}' → '{standard_name}'")
        
        # Add missing columns with defaults
        missing_columns = self.validate_columns()
        
        for required_col in missing_columns:
            if required_col == 'Industry':
                # Try to extract industry from company names or add default
                self.df[required_col] = 'E-commerce'  # Default for most VOC interviews
                self.fixes_applied.append(f"Added '{required_col}' with default value 'E-commerce'")
                print(f"   ✅ Added '{required_col}' with default value 'E-commerce'")
                
            elif required_col == 'Interview Status':
                self.df[required_col] = 'Completed'
                self.fixes_applied.append(f"Added '{required_col}' with default value 'Completed'")
                print(f"   ✅ Added '{required_col}' with default value 'Completed'")
                
            elif required_col == 'Completion Date':
                # Try to find any date column
                date_columns = [col for col in self.df.columns if 'date' in col.lower() or 'Date' in col]
                if date_columns:
                    self.df[required_col] = self.df[date_columns[0]]
                    self.fixes_applied.append(f"Copied '{date_columns[0]}' to '{required_col}'")
                    print(f"   ✅ Copied '{date_columns[0]}' to '{required_col}'")
                else:
                    self.df[required_col] = pd.Timestamp.now().strftime('%Y-%m-%d')
                    self.fixes_applied.append(f"Added '{required_col}' with current date")
                    print(f"   ✅ Added '{required_col}' with current date")
        
        return True
    
    def validate_data_quality(self) -> List[str]:
        """Check data quality issues"""
        if self.df is None:
            return []
        
        quality_issues = []
        
        # Check for empty transcripts
        if 'Raw Transcript' in self.df.columns:
            empty_transcripts = self.df['Raw Transcript'].isna().sum()
            if empty_transcripts > 0:
                quality_issues.append(f"⚠️ {empty_transcripts} interviews have empty transcripts")
        
        # Check for very short transcripts
        if 'Raw Transcript' in self.df.columns:
            short_transcripts = 0
            for transcript in self.df['Raw Transcript'].dropna():
                if len(str(transcript).strip()) < 50:
                    short_transcripts += 1
            
            if short_transcripts > 0:
                quality_issues.append(f"⚠️ {short_transcripts} interviews have very short transcripts (<50 chars)")
        
        # Check for missing company names
        if 'Interview Contact Company Name' in self.df.columns:
            missing_companies = self.df['Interview Contact Company Name'].isna().sum()
            if missing_companies > 0:
                quality_issues.append(f"⚠️ {missing_companies} interviews missing company names")
        
        # Check for missing interviewee names
        if 'Interview Contact Full Name' in self.df.columns:
            missing_names = self.df['Interview Contact Full Name'].isna().sum()
            if missing_names > 0:
                quality_issues.append(f"⚠️ {missing_names} interviews missing interviewee names")
        
        return quality_issues
    
    def extract_company_names(self) -> bool:
        """Extract company names from transcript data if missing"""
        if self.df is None or 'Raw Transcript' not in self.df.columns:
            return False
        
        if 'Interview Contact Company Name' not in self.df.columns:
            return False
        
        print(f"🏢 Extracting company names from transcripts...")
        
        for idx, row in self.df.iterrows():
            if pd.isna(row['Interview Contact Company Name']) and not pd.isna(row['Raw Transcript']):
                transcript = str(row['Raw Transcript'])
                
                # Look for company patterns in transcript
                company = self._extract_company_from_text(transcript)
                
                if company:
                    self.df.at[idx, 'Interview Contact Company Name'] = company
                    self.fixes_applied.append(f"Extracted company '{company}' from transcript for row {idx}")
                    print(f"   ✅ Extracted company '{company}' from transcript")
        
        return True
    
    def _extract_company_from_text(self, text: str) -> Optional[str]:
        """Extract company name from transcript text"""
        if not text:
            return None
        
        # Common patterns for company names
        patterns = [
            r'Company Snapshot\s*([^\n]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Company|Inc|LLC|Corp|Ltd)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+is\s+(?:a|an)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+operates',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 3 and len(company) < 100:
                    return company
        
        return None
    
    def save_fixed_csv(self, output_path: str = None) -> str:
        """Save the fixed CSV file"""
        if self.df is None:
            return ""
        
        if output_path is None:
            base_name = Path(self.csv_path).stem
            output_path = f"{base_name}_VALIDATED.csv"
        
        self.df.to_csv(output_path, index=False)
        print(f"💾 Fixed CSV saved to: {output_path}")
        
        return output_path
    
    def generate_report(self) -> str:
        """Generate validation report"""
        report = []
        report.append("=" * 80)
        report.append("CSV VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"File: {self.csv_path}")
        report.append(f"Shape: {self.df.shape if self.df is not None else 'N/A'}")
        report.append("")
        
        # Column validation results
        missing_columns = self.validate_columns()
        if missing_columns:
            report.append("❌ MISSING REQUIRED COLUMNS:")
            for col, variations in missing_columns.items():
                report.append(f"   - {col}")
                report.append(f"     Expected variations: {', '.join(variations)}")
            report.append("")
        else:
            report.append("✅ ALL REQUIRED COLUMNS PRESENT")
            report.append("")
        
        # Fixes applied
        if self.fixes_applied:
            report.append("🔧 AUTO-FIXES APPLIED:")
            for fix in self.fixes_applied:
                report.append(f"   - {fix}")
            report.append("")
        
        # Data quality issues
        quality_issues = self.validate_data_quality()
        if quality_issues:
            report.append("⚠️ DATA QUALITY ISSUES:")
            for issue in quality_issues:
                report.append(f"   - {issue}")
            report.append("")
        else:
            report.append("✅ NO DATA QUALITY ISSUES DETECTED")
            report.append("")
        
        # Final validation
        final_missing = self.validate_columns()
        if final_missing:
            report.append("❌ VALIDATION FAILED - Manual fixes required:")
            for col in final_missing:
                report.append(f"   - {col}")
        else:
            report.append("✅ CSV VALIDATION PASSED - Ready for processing!")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def validate_and_fix(self) -> Tuple[bool, str]:
        """Main validation and fixing process"""
        print(f"🔍 Validating CSV: {self.csv_path}")
        
        # Load CSV
        if not self.load_csv():
            return False, "Failed to load CSV file"
        
        # Initial validation
        missing_columns = self.validate_columns()
        print(f"📊 Initial validation: {len(missing_columns)} missing columns")
        
        # Auto-fix issues
        if missing_columns:
            print(f"🔧 Attempting auto-fixes...")
            self.auto_fix_columns()
            self.extract_company_names()
        
        # Final validation
        final_missing = self.validate_columns()
        quality_issues = self.validate_data_quality()
        
        # Generate report
        report = self.generate_report()
        
        # Determine if validation passed
        validation_passed = len(final_missing) == 0
        
        return validation_passed, report

def main():
    """Main function for command line usage"""
    if len(sys.argv) != 2:
        print("Usage: python csv_validator.py <csv_file>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        sys.exit(1)
    
    # Run validation
    validator = CSVValidator(csv_path)
    success, report = validator.validate_and_fix()
    
    # Print report
    print(report)
    
    # Save fixed CSV if validation passed
    if success:
        output_path = validator.save_fixed_csv()
        print(f"\n🎉 CSV is ready for processing!")
        print(f"📁 Use this file: {output_path}")
    else:
        print(f"\n❌ CSV validation failed - manual fixes required")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 