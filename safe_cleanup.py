#!/usr/bin/env python3
"""
Safe Cleanup Script
Executes cleanup plan with safety checks
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

class SafeCleanup:
    def __init__(self):
        self.backup_dir = "cleanup_backup"
        self.removed_files = []
        
    def create_backup(self):
        """Create backup of files before removal"""
        print("📦 Creating backup...")
        
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir)
        
        os.makedirs(self.backup_dir)
        
        # Files to backup before removal
        files_to_backup = [
            'app_backup.py', 'app_broken.py', 'app_clean.py', 
            'app_original.py', 'app_temp.py', 'app_nomarkdown.py'
        ]
        
        for file in files_to_backup:
            if os.path.exists(file):
                shutil.copy2(file, self.backup_dir)
                print(f"  ✅ Backed up {file}")
        
        # Backup debug files
        debug_files = [f for f in os.listdir('.') if f.startswith('debug_') and f.endswith('.py')]
        for file in debug_files:
            shutil.copy2(file, self.backup_dir)
            print(f"  ✅ Backed up {file}")
        
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
    
    def remove_safe_files(self):
        """Remove files that are safe to delete"""
        print("🗑️ Removing safe files...")
        
        # Backup/broken files
        backup_files = [
            'app_backup.py', 'app_broken.py', 'app_clean.py',
            'app_original.py', 'app_temp.py', 'app_nomarkdown.py'
        ]
        
        for file in backup_files:
            if os.path.exists(file):
                os.remove(file)
                self.removed_files.append(file)
                print(f"  ✅ Removed {file}")
        
        # Debug files
        debug_files = [f for f in os.listdir('.') if f.startswith('debug_') and f.endswith('.py')]
        for file in debug_files:
            os.remove(file)
            self.removed_files.append(file)
            print(f"  ✅ Removed {file}")
        
        # Test debug files
        test_debug_files = [f for f in os.listdir('.') if f.startswith('test_debug_') and f.endswith('.py')]
        for file in test_debug_files:
            os.remove(file)
            self.removed_files.append(file)
            print(f"  ✅ Removed {file}")
        
        # Stage4b files
        stage4b_files = [f for f in os.listdir('.') if f.startswith('stage4b_') and f.endswith('.py')]
        for file in stage4b_files:
            os.remove(file)
            self.removed_files.append(file)
            print(f"  ✅ Removed {file}")
        
        # Test result files
        test_result_files = [f for f in os.listdir('.') if 'test_results' in f and f.endswith('.json')]
        for file in test_result_files:
            os.remove(file)
            self.removed_files.append(file)
            print(f"  ✅ Removed {file}")
    
    def verify_modules(self):
        """Verify if modules are being used"""
        print("🔍 Verifying modules...")
        
        modules_to_check = ['coders', 'loaders', 'validators', 'prompts']
        
        for module in modules_to_check:
            if os.path.exists(module):
                try:
                    # Try to import the module
                    result = subprocess.run([sys.executable, '-c', f"import {module}; print('{module} module works')"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        print(f"  ✅ {module} module is working")
                    else:
                        print(f"  ⚠️ {module} module has issues: {result.stderr}")
                except Exception as e:
                    print(f"  ❌ {module} module failed: {e}")
    
    def generate_report(self):
        """Generate cleanup report"""
        print("\n" + "="*50)
        print("📊 CLEANUP REPORT")
        print("="*50)
        
        print(f"\n🗑️ Files Removed ({len(self.removed_files)}):")
        for file in sorted(self.removed_files):
            print(f"  - {file}")
        
        print(f"\n📦 Backup Location: {self.backup_dir}")
        print(f"📦 Backup contains {len(os.listdir(self.backup_dir))} files")
        
        print(f"\n🎯 Next Steps:")
        print("  1. Test the system thoroughly")
        print("  2. If everything works, commit changes")
        print("  3. If issues arise, restore from backup")
        print("  4. Continue with Phase 2 (module verification)")
    
    def run_cleanup(self):
        """Run the complete cleanup process"""
        print("🧹 Starting Safe Cleanup Process")
        print("="*50)
        
        # Step 1: Create backup
        self.create_backup()
        
        # Step 2: Test before cleanup
        print("\n🧪 Pre-cleanup testing...")
        if not self.test_core_functionality():
            print("❌ Pre-cleanup tests failed. Aborting cleanup.")
            return False
        
        # Step 3: Remove safe files
        self.remove_safe_files()
        
        # Step 4: Test after cleanup
        print("\n🧪 Post-cleanup testing...")
        if not self.test_core_functionality():
            print("❌ Post-cleanup tests failed. Restoring from backup...")
            self.restore_backup()
            return False
        
        # Step 5: Verify modules
        self.verify_modules()
        
        # Step 6: Generate report
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
    cleanup = SafeCleanup()
    
    print("🧹 Safe Cleanup Tool")
    print("This will remove backup, debug, and test files safely.")
    
    response = input("\nContinue with cleanup? (y/N): ")
    if response.lower() != 'y':
        print("Cleanup cancelled.")
        return
    
    success = cleanup.run_cleanup()
    
    if success:
        print("\n✅ Cleanup completed successfully!")
        print("💡 Remember to test the system thoroughly before committing.")
    else:
        print("\n❌ Cleanup failed. System restored from backup.")

if __name__ == "__main__":
    main() 