#!/usr/bin/env python3
"""
Comprehensive Cleanup Script
Removes experimental features (Stage 4B/5) and cleans up the codebase
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

class ComprehensiveCleanup:
    def __init__(self):
        self.backup_dir = "experimental_cleanup_backup"
        self.removed_files = []
        self.ui_changes = []
        
    def create_backup(self):
        """Create backup of experimental files before removal"""
        print("📦 Creating backup of experimental files...")
        
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir)
        
        os.makedirs(self.backup_dir)
        
        # Files to backup before removal
        experimental_files = [
            'stage4b_scorecard_analyzer.py',
            'stage5_executive_analyzer.py', 
            'scorecard_theme_ui.py',
            'import_scorecard_themes.py'
        ]
        
        for file in experimental_files:
            if os.path.exists(file):
                shutil.copy2(file, self.backup_dir)
                print(f"  ✅ Backed up {file}")
        
        # Backup app.py before modifying
        if os.path.exists('app.py'):
            shutil.copy2('app.py', os.path.join(self.backup_dir, 'app_backup.py'))
            print(f"  ✅ Backed up app.py")
        
        print(f"📦 Backup created in {self.backup_dir}")
    
    def test_core_functionality(self):
        """Test core functionality"""
        print("🧪 Testing core functionality...")
        
        tests = [
            ("Stage 3", "from stage3_findings_analyzer import Stage3FindingsAnalyzer; print('Stage 3 works')"),
            ("Stage 4", "from stage4_theme_analyzer import Stage4ThemeAnalyzer; print('Stage 4 works')"),
            ("Database", "from supabase_database import SupabaseDatabase; print('Database works')"),
        ]
        
        all_passed = True
        for test_name, test_code in tests:
            try:
                result = subprocess.run([sys.executable, '-c', test_code], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"  ✅ {test_name} test passed")
                else:
                    print(f"  ❌ {test_name} test failed: {result.stderr}")
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {test_name} test failed: {e}")
                all_passed = False
        
        return all_passed
    
    def remove_experimental_files(self):
        """Remove experimental files"""
        print("🗑️ Removing experimental files...")
        
        experimental_files = [
            'stage4b_scorecard_analyzer.py',
            'stage5_executive_analyzer.py',
            'scorecard_theme_ui.py',
            'import_scorecard_themes.py'
        ]
        
        for file in experimental_files:
            if os.path.exists(file):
                os.remove(file)
                self.removed_files.append(file)
                print(f"  ✅ Removed {file}")
    
    def clean_app_py(self):
        """Clean up app.py to remove experimental features"""
        print("🧹 Cleaning app.py...")
        
        if not os.path.exists('app.py'):
            print("  ❌ app.py not found")
            return False
        
        # Read app.py
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove experimental imports and code
        changes_made = []
        
        # Remove scorecard theme imports and code
        if 'from scorecard_theme_ui import display_scorecard_themes' in content:
            content = content.replace('from scorecard_theme_ui import display_scorecard_themes', '')
            changes_made.append('Removed scorecard_theme_ui import')
        
        # Remove stage4b page
        stage4b_section = """elif page == "stage4b":
        st.title("🗂️ Stage 4B: Generate Scorecard Themes")
        st.write("DEBUG: Stage 4B page loaded")

        if not SUPABASE_AVAILABLE:
            st.error("❌ Database not available")
        else:
            stage2_summary = get_stage2_summary()
            if not stage2_summary or stage2_summary.get('quotes_with_scores', 0) == 0:
                st.info("📊 Please run Stage 2 quote scoring first")
            else:
                from scorecard_theme_ui import display_scorecard_themes
                client_id = get_client_id()
                db = SupabaseDatabase()
                try:
                    response = db.supabase.table('scorecard_themes').select('*').eq('client_id', client_id).execute()
                    existing_themes = response.data
                except Exception as e:
                    existing_themes = []
                if existing_themes:
                    st.success(f"✅ Found {len(existing_themes)} existing scorecard themes")
                    display_scorecard_themes(client_id)
                else:
                    st.info("📊 No scorecard themes found. Generate them using the button below.")
                    if st.button("🚀 Generate Scorecard Themes", type="primary", help="Generate scorecard-driven themes with semantic merging"):
                        from stage4b_scorecard_analyzer import Stage4BScorecardAnalyzer
                        with st.spinner("Generating scorecard themes with semantic merging..."):
                            analyzer = Stage4BScorecardAnalyzer()
                            result = analyzer.process_scorecard_themes(client_id=client_id)
                            if result and result.get('status') == 'success':
                                st.success(f"✅ Scorecard theme generation complete! Generated {result.get('scorecard_themes_generated', 0)} themes")
                                st.rerun()
                            else:
                                st.error(f"❌ Scorecard theme generation failed: {result.get('message', 'Unknown error')}")"""
        
        if stage4b_section in content:
            content = content.replace(stage4b_section, '')
            changes_made.append('Removed stage4b page')
        
        # Remove stage5 page
        stage5_section = """elif page == "stage5":
        st.title("🎯 Stage 5: Executive Synthesis")
        st.write("DEBUG: Stage 5 page loaded")

        if not SUPABASE_AVAILABLE:
            st.error("❌ Database not available")
        else:
            from stage5_executive_analyzer import Stage5ExecutiveAnalyzer
            client_id = get_client_id()
            
            # Check for existing executive themes
            db = SupabaseDatabase()
            try:
                response = db.supabase.table('executive_themes').select('*').eq('client_id', client_id).execute()
                existing_themes = response.data
            except Exception as e:
                existing_themes = []
            
            if existing_themes:
                st.success(f"✅ Found {len(existing_themes)} existing executive themes")
                show_stage5_executive_themes()
            else:
                st.info("📊 No executive themes found. Generate them using the button below.")
                if st.button("🚀 Generate Executive Synthesis", type="primary", help="Generate executive synthesis with criteria scorecard"):
                    with st.spinner("Generating executive synthesis..."):
                        analyzer = Stage5ExecutiveAnalyzer()
                        result = analyzer.process_executive_synthesis(client_id=client_id)
                        if result and result.get('status') == 'success':
                            st.success(f"✅ Generated {result.get('executive_themes_generated', 0)} executive themes!")
                            st.rerun()
                        else:
                            st.error(f"❌ Executive synthesis failed: {result.get('message', 'Unknown error')}")"""
        
        if stage5_section in content:
            content = content.replace(stage5_section, '')
            changes_made.append('Removed stage5 page')
        
        # Remove executive themes functions
        executive_functions = [
            'def show_stage5_executive_themes():',
            'def show_stage5_criteria_scorecard():',
            'def get_executive_themes_summary():'
        ]
        
        for func in executive_functions:
            if func in content:
                # Find the function and remove it
                start = content.find(func)
                if start != -1:
                    # Find the end of the function (next function or end of file)
                    lines = content[start:].split('\n')
                    func_lines = []
                    brace_count = 0
                    for i, line in enumerate(lines):
                        if line.strip().startswith('def ') and i > 0:
                            break
                        func_lines.append(line)
                        if '{' in line:
                            brace_count += line.count('{')
                        if '}' in line:
                            brace_count -= line.count('}')
                        if brace_count == 0 and line.strip() == '':
                            break
                    
                    func_content = '\n'.join(func_lines)
                    content = content.replace(func_content, '')
                    changes_made.append(f'Removed {func}')
        
        # Remove experimental navigation items
        nav_items_to_remove = [
            '"stage4b": "🗂️ Stage 4B: Scorecard Themes",',
            '"stage5": "🎯 Stage 5: Executive Synthesis",'
        ]
        
        for item in nav_items_to_remove:
            if item in content:
                content = content.replace(item, '')
                changes_made.append(f'Removed navigation item: {item}')
        
        # Write cleaned app.py
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        if changes_made:
            print(f"  ✅ Made {len(changes_made)} changes to app.py")
            for change in changes_made:
                print(f"    - {change}")
            self.ui_changes = changes_made
        else:
            print("  ℹ️ No changes needed in app.py")
        
        return True
    
    def generate_cleanup_sql(self):
        """Generate SQL for database cleanup"""
        print("📝 Generating cleanup SQL...")
        
        sql_commands = [
            "-- Remove unused columns from themes table",
            "ALTER TABLE themes DROP COLUMN IF EXISTS fuzzy_match_score;",
            "ALTER TABLE themes DROP COLUMN IF EXISTS semantic_group_id;",
            "ALTER TABLE themes DROP COLUMN IF EXISTS scorecard_theme_id;",
            "ALTER TABLE themes DROP COLUMN IF EXISTS synthesis_theme_id;",
            "",
            "-- Remove unused columns from enhanced_findings table",
            "ALTER TABLE enhanced_findings DROP COLUMN IF EXISTS scorecard_criterion_priority;",
            "ALTER TABLE enhanced_findings DROP COLUMN IF EXISTS sentiment_alignment_score;",
            "",
            "-- Remove experimental tables",
            "DROP TABLE IF EXISTS scorecard_themes;",
            "DROP TABLE IF EXISTS executive_themes;",
            "DROP TABLE IF EXISTS criteria_scorecard;",
            "",
            "-- Check for views (run this in Supabase dashboard)",
            "-- SELECT schemaname, viewname FROM pg_views WHERE schemaname = 'public';"
        ]
        
        with open('experimental_cleanup.sql', 'w') as f:
            f.write("-- Experimental Feature Cleanup SQL\n")
            f.write("-- Generated automatically - review before running\n\n")
            f.write("\n".join(sql_commands))
        
        print(f"  ✅ Generated experimental_cleanup.sql")
    
    def generate_report(self):
        """Generate cleanup report"""
        print("\n" + "="*50)
        print("📊 COMPREHENSIVE CLEANUP REPORT")
        print("="*50)
        
        print(f"\n🗑️ Files Removed ({len(self.removed_files)}):")
        for file in sorted(self.removed_files):
            print(f"  - {file}")
        
        print(f"\n🧹 UI Changes Made ({len(self.ui_changes)}):")
        for change in self.ui_changes:
            print(f"  - {change}")
        
        print(f"\n📦 Backup Location: {self.backup_dir}")
        print(f"📦 Backup contains {len(os.listdir(self.backup_dir))} files")
        
        print(f"\n🎯 Next Steps:")
        print("  1. Execute experimental_cleanup.sql in Supabase dashboard")
        print("  2. Test the system thoroughly")
        print("  3. If everything works, commit changes")
        print("  4. If issues arise, restore from backup")
        
        print(f"\n💡 Benefits:")
        print("  - Removed 3 experimental tables")
        print("  - Removed 6 unused columns")
        print("  - Simplified codebase to core pipeline only")
        print("  - Cleaner database schema")
    
    def run_cleanup(self):
        """Run the complete cleanup process"""
        print("🧹 Starting Comprehensive Cleanup Process")
        print("="*50)
        
        # Step 1: Create backup
        self.create_backup()
        
        # Step 2: Test before cleanup
        print("\n🧪 Pre-cleanup testing...")
        if not self.test_core_functionality():
            print("❌ Pre-cleanup tests failed. Aborting cleanup.")
            return False
        
        # Step 3: Remove experimental files
        self.remove_experimental_files()
        
        # Step 4: Clean app.py
        self.clean_app_py()
        
        # Step 5: Test after cleanup
        print("\n🧪 Post-cleanup testing...")
        if not self.test_core_functionality():
            print("❌ Post-cleanup tests failed. Restoring from backup...")
            self.restore_backup()
            return False
        
        # Step 6: Generate cleanup SQL
        self.generate_cleanup_sql()
        
        # Step 7: Generate report
        self.generate_report()
        
        return True
    
    def restore_backup(self):
        """Restore files from backup"""
        print("🔄 Restoring from backup...")
        
        if os.path.exists(self.backup_dir):
            for file in os.listdir(self.backup_dir):
                src = os.path.join(self.backup_dir, file)
                dst = file
                shutil.copy2(src, dst)
                print(f"  ✅ Restored {file}")
        
        print("✅ Backup restoration complete")

def main():
    cleanup = ComprehensiveCleanup()
    
    print("🧹 Comprehensive Experimental Feature Cleanup")
    print("This will remove Stage 4B and Stage 5 experimental features.")
    
    response = input("\nContinue with cleanup? (y/N): ")
    if response.lower() != 'y':
        print("Cleanup cancelled.")
        return
    
    success = cleanup.run_cleanup()
    
    if success:
        print("\n✅ Comprehensive cleanup completed successfully!")
        print("💡 Remember to execute experimental_cleanup.sql in Supabase dashboard.")
    else:
        print("\n❌ Cleanup failed. System restored from backup.")

if __name__ == "__main__":
    main() 