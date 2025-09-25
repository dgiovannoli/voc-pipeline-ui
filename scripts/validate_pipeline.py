#!/usr/bin/env python3
"""
Pipeline Validation Master Script
Runs all validation checks in sequence before VOC pipeline processing
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from csv_validator import CSVValidator
from database_validator import DatabaseValidator
from theme_limiter import ThemeLimiter
from data_quality_dashboard import DataQualityDashboard

class PipelineValidator:
    """Master validation system for VOC pipeline"""
    
    def __init__(self, client_id: str, csv_path: str = None):
        self.client_id = client_id
        self.csv_path = csv_path
        self.validation_results = {}
        self.overall_status = True
        
    def validate_csv(self) -> bool:
        """Validate CSV file if provided"""
        if not self.csv_path:
            print("📋 No CSV file provided - skipping CSV validation")
            return True
        
        if not os.path.exists(self.csv_path):
            print(f"❌ CSV file not found: {self.csv_path}")
            return False
        
        print(f"🔍 Validating CSV: {self.csv_path}")
        validator = CSVValidator(self.csv_path)
        success, report = validator.validate_and_fix()
        
        self.validation_results['csv'] = {
            'success': success,
            'report': report
        }
        
        if success:
            print("✅ CSV validation passed")
            # Save the path to the validated CSV
            self.validated_csv_path = validator.save_fixed_csv()
        else:
            print("❌ CSV validation failed")
            self.overall_status = False
        
        return success
    
    def validate_database(self) -> bool:
        """Validate database schema and constraints"""
        print(f"🗄️ Validating database schema...")
        validator = DatabaseValidator(self.client_id)
        success, report = validator.validate_schema()
        
        self.validation_results['database'] = {
            'success': success,
            'report': report
        }
        
        if success:
            print("✅ Database validation passed")
        else:
            print("❌ Database validation failed")
            self.overall_status = False
        
        return success
    
    def check_theme_limits(self) -> bool:
        """Check if theme generation is within limits"""
        print(f"🎯 Checking theme generation limits...")
        limiter = ThemeLimiter(self.client_id)
        report = limiter.generate_limits_report()
        
        # Check if there are violations
        has_violations = '❌ LIMITS VIOLATIONS DETECTED' in report
        
        self.validation_results['theme_limits'] = {
            'success': not has_violations,
            'report': report
        }
        
        if not has_violations:
            print("✅ Theme limits check passed")
        else:
            print("⚠️ Theme limits violations detected")
            # This is a warning, not a critical failure
        
        return True  # Always return True as this is not critical
    
    def check_data_quality(self) -> bool:
        """Run comprehensive data quality check"""
        print(f"🔍 Running data quality dashboard...")
        dashboard = DataQualityDashboard(self.client_id)
        success, report = dashboard.run_quality_check()
        
        self.validation_results['data_quality'] = {
            'success': success,
            'report': report
        }
        
        if success:
            print("✅ Data quality check passed")
        else:
            print("❌ Data quality issues detected")
            self.overall_status = False
        
        return success
    
    def generate_summary_report(self) -> str:
        """Generate comprehensive validation summary"""
        report = []
        report.append("=" * 80)
        report.append("VOC PIPELINE VALIDATION SUMMARY")
        report.append("=" * 80)
        report.append(f"Client: {self.client_id}")
        report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # CSV validation results
        if 'csv' in self.validation_results:
            csv_result = self.validation_results['csv']
            status = "✅ PASSED" if csv_result['success'] else "❌ FAILED"
            report.append(f"📋 CSV Validation: {status}")
            if csv_result['success'] and hasattr(self, 'validated_csv_path'):
                report.append(f"   📁 Validated file: {self.validated_csv_path}")
            report.append("")
        
        # Database validation results
        if 'database' in self.validation_results:
            db_result = self.validation_results['database']
            status = "✅ PASSED" if db_result['success'] else "❌ FAILED"
            report.append(f"🗄️ Database Validation: {status}")
            report.append("")
        
        # Theme limits results
        if 'theme_limits' in self.validation_results:
            theme_result = self.validation_results['theme_limits']
            status = "✅ PASSED" if theme_result['success'] else "⚠️ WARNINGS"
            report.append(f"🎯 Theme Limits Check: {status}")
            report.append("")
        
        # Data quality results
        if 'data_quality' in self.validation_results:
            dq_result = self.validation_results['data_quality']
            status = "✅ PASSED" if dq_result['success'] else "❌ FAILED"
            report.append(f"🔍 Data Quality Check: {status}")
            report.append("")
        
        # Overall status
        report.append("📊 OVERALL VALIDATION STATUS:")
        if self.overall_status:
            report.append("🎉 ALL CRITICAL VALIDATIONS PASSED")
            report.append("   Pipeline is ready for processing")
            if hasattr(self, 'validated_csv_path'):
                report.append(f"   Use validated CSV: {self.validated_csv_path}")
        else:
            report.append("❌ VALIDATION FAILED")
            report.append("   Fix critical issues before processing")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_full_validation(self) -> Tuple[bool, str]:
        """Run complete validation pipeline"""
        print(f"🚀 Starting VOC pipeline validation for client: {self.client_id}")
        print("=" * 80)
        
        # Step 1: CSV validation
        if self.csv_path:
            if not self.validate_csv():
                return False, "CSV validation failed"
        
        # Step 2: Database validation
        if not self.validate_database():
            return False, "Database validation failed"
        
        # Step 3: Theme limits check
        self.check_theme_limits()
        
        # Step 4: Data quality check
        if not self.check_data_quality():
            return False, "Data quality check failed"
        
        # Generate summary report
        summary = self.generate_summary_report()
        
        return self.overall_status, summary

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Run complete VOC pipeline validation')
    parser.add_argument('--client', required=True, help='Client ID to validate')
    parser.add_argument('--csv', help='Path to CSV file for validation')
    parser.add_argument('--output', help='Output file for validation report')
    args = parser.parse_args()
    
    # Import datetime here to avoid circular import
    from datetime import datetime
    
    # Run validation
    validator = PipelineValidator(args.client, args.csv)
    success, report = validator.run_full_validation()
    
    # Print report
    print(report)
    
    # Save report to file if requested
    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"\n📄 Validation report saved to: {args.output}")
        except Exception as e:
            print(f"⚠️ Could not save report to {args.output}: {e}")
    
    if success:
        print(f"\n🎉 Pipeline validation completed successfully!")
        if hasattr(validator, 'validated_csv_path'):
            print(f"💡 Use this validated CSV: {validator.validated_csv_path}")
    else:
        print(f"\n❌ Pipeline validation failed - fix issues before processing")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 