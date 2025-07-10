#!/usr/bin/env python3
"""
Database Cleanup Analysis
Analyzes database schema and usage to identify unused tables and columns
"""

import os
import sys
from supabase_database import SupabaseDatabase

class DatabaseCleanupAnalyzer:
    def __init__(self):
        self.db = SupabaseDatabase()
        self.tables = {}
        self.unused_tables = []
        self.unused_columns = {}
        
    def analyze_schema(self):
        """Analyze current database schema"""
        print("🔍 Analyzing database schema...")
        
        # Get all tables
        try:
            # Check core tables
            core_tables = ['stage1_data_responses', 'stage3_findings', 'themes']
            
            for table in core_tables:
                try:
                    result = self.db.supabase.table(table).select('count').execute()
                    count = len(result.data) if result.data else 0
                    self.tables[table] = {
                        'exists': True,
                        'count': count,
                        'columns': []
                    }
                    print(f"  ✅ {table}: {count} rows")
                except Exception as e:
                    print(f"  ❌ {table}: {e}")
                    self.tables[table] = {'exists': False, 'count': 0, 'columns': []}
            
            # Check other tables
            other_tables = ['quote_analyses', 'scorecard_themes']
            for table in other_tables:
                try:
                    result = self.db.supabase.table(table).select('count').execute()
                    count = len(result.data) if result.data else 0
                    self.tables[table] = {
                        'exists': True,
                        'count': count,
                        'columns': []
                    }
                    print(f"  ⚠️ {table}: {count} rows (potential unused table)")
                except Exception as e:
                    print(f"  ❌ {table}: {e}")
                    self.tables[table] = {'exists': False, 'count': 0, 'columns': []}
                    
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        return True
    
    def analyze_column_usage(self):
        """Analyze which columns are actually used"""
        print("\n🔍 Analyzing column usage...")
        
        # Check themes table columns
        if self.tables.get('themes', {}).get('exists'):
            try:
                # Get sample data to see which columns have values
                result = self.db.supabase.table('stage4_themes').select('*').limit(5).execute()
                if result.data:
                    sample = result.data[0]
                    used_columns = [col for col, val in sample.items() if val is not None]
                    all_columns = list(sample.keys())
                    unused_columns = [col for col in all_columns if col not in used_columns]
                    
                    print(f"  📊 themes table columns:")
                    print(f"    Used: {used_columns}")
                    print(f"    Potentially unused: {unused_columns}")
                    
                    self.unused_columns['themes'] = unused_columns
            except Exception as e:
                print(f"  ❌ Error analyzing themes columns: {e}")
        
        # Check stage3_findings table columns
        if self.tables.get('stage3_findings', {}).get('exists'):
            try:
                result = self.db.supabase.table('stage3_findings').select('*').limit(5).execute()
                if result.data:
                    sample = result.data[0]
                    used_columns = [col for col, val in sample.items() if val is not None]
                    all_columns = list(sample.keys())
                    unused_columns = [col for col in all_columns if col not in used_columns]
                    
                    print(f"  📊 stage3_findings table columns:")
                    print(f"    Used: {used_columns}")
                    print(f"    Potentially unused: {unused_columns}")
                    
                    self.unused_columns['stage3_findings'] = unused_columns
            except Exception as e:
                print(f"  ❌ Error analyzing stage3_findings columns: {e}")
    
    def check_table_usage(self):
        """Check if tables are actually being used in the code"""
        print("\n🔍 Checking table usage in code...")
        
        # Check if quote_analyses table is used
        quote_analyses_used = False
        try:
            # Search for quote_analyses usage in code
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if 'quote_analyses' in content:
                                    quote_analyses_used = True
                                    print(f"  📄 quote_analyses used in: {file_path}")
                        except Exception:
                            continue
        except Exception as e:
            print(f"  ❌ Error checking quote_analyses usage: {e}")
        
        if not quote_analyses_used and self.tables.get('quote_analyses', {}).get('count', 0) == 0:
            self.unused_tables.append('quote_analyses')
            print(f"  🗑️ quote_analyses table appears unused")
        
        # Check if scorecard_themes table is used
        scorecard_themes_used = False
        try:
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if 'scorecard_themes' in content:
                                    scorecard_themes_used = True
                                    print(f"  📄 scorecard_themes used in: {file_path}")
                        except Exception:
                            continue
        except Exception as e:
            print(f"  ❌ Error checking scorecard_themes usage: {e}")
        
        if not scorecard_themes_used and self.tables.get('scorecard_themes', {}).get('count', 0) == 0:
            self.unused_tables.append('scorecard_themes')
            print(f"  🗑️ scorecard_themes table appears unused")
    
    def generate_cleanup_sql(self):
        """Generate SQL for database cleanup"""
        print("\n📝 Generating cleanup SQL...")
        
        sql_commands = []
        
        # Drop unused tables
        for table in self.unused_tables:
            sql_commands.append(f"-- Drop unused table\nDROP TABLE IF EXISTS {table};")
        
        # Drop unused columns
        for table, columns in self.unused_columns.items():
            for column in columns:
                sql_commands.append(f"-- Drop unused column from {table}\nALTER TABLE {table} DROP COLUMN IF EXISTS {column};")
        
        if sql_commands:
            with open('database_cleanup.sql', 'w') as f:
                f.write("-- Database Cleanup Script\n")
                f.write("-- Generated automatically - review before running\n\n")
                f.write("\n".join(sql_commands))
            
            print(f"  ✅ Generated database_cleanup.sql with {len(sql_commands)} commands")
        else:
            print("  ℹ️ No cleanup SQL needed")
    
    def generate_report(self):
        """Generate comprehensive cleanup report"""
        print("\n" + "="*50)
        print("📊 DATABASE CLEANUP REPORT")
        print("="*50)
        
        print(f"\n🗄️ Table Analysis:")
        for table, info in self.tables.items():
            status = "✅" if info['exists'] else "❌"
            print(f"  {status} {table}: {info['count']} rows")
        
        print(f"\n🗑️ Unused Tables ({len(self.unused_tables)}):")
        for table in self.unused_tables:
            print(f"  - {table}")
        
        print(f"\n🗑️ Potentially Unused Columns:")
        for table, columns in self.unused_columns.items():
            if columns:
                print(f"  {table}: {columns}")
        
        print(f"\n🎯 Recommendations:")
        if self.unused_tables:
            print("  1. Drop unused tables (if confirmed)")
        if any(self.unused_columns.values()):
            print("  2. Review and drop unused columns")
        print("  3. Test system after any schema changes")
        print("  4. Backup database before making changes")
    
    def run_analysis(self):
        """Run complete database analysis"""
        print("🔍 Starting Database Cleanup Analysis")
        print("="*50)
        
        if not self.analyze_schema():
            return False
        
        self.analyze_column_usage()
        self.check_table_usage()
        self.generate_cleanup_sql()
        self.generate_report()
        
        return True

def main():
    analyzer = DatabaseCleanupAnalyzer()
    
    print("🔍 Database Cleanup Analysis Tool")
    print("This will analyze your database schema and identify unused tables/columns.")
    
    response = input("\nContinue with analysis? (y/N): ")
    if response.lower() != 'y':
        print("Analysis cancelled.")
        return
    
    success = analyzer.run_analysis()
    
    if success:
        print("\n✅ Database analysis completed!")
        print("💡 Review database_cleanup.sql before running any commands.")
    else:
        print("\n❌ Database analysis failed.")

if __name__ == "__main__":
    main() 