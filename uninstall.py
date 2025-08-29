#!/usr/bin/env python3
"""
Uninstall script for AI Intelligence Briefing System
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import json


class BriefingUninstaller:
    """Handles complete uninstallation of the briefing system"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.home_dir = Path.home()
        self.venv_path = self.base_dir / "venv"
        
        # LaunchAgent paths
        self.launchd_dir = self.home_dir / "Library" / "LaunchAgents"
        self.plist_name = "com.ai.intelligence.briefing"
        self.plist_path = self.launchd_dir / f"{self.plist_name}.plist"
    
    def print_step(self, step_num: int, total_steps: int, description: str):
        """Print uninstallation step with progress"""
        print(f"\n[{step_num}/{total_steps}] {description}")
        print("-" * 50)
    
    def run_command(self, command: list, description: str = "", ignore_errors: bool = True) -> bool:
        """Run a command and return success status"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                if description:
                    print(f"✓ {description}")
                return True
            else:
                if ignore_errors:
                    print(f"? {description} (already removed or not found)")
                    return True
                else:
                    print(f"✗ Failed: {description}")
                    if result.stderr:
                        print(f"Error: {result.stderr}")
                    return False
                    
        except subprocess.TimeoutExpired:
            print(f"? Timeout: {description}")
            return ignore_errors
        except Exception as e:
            if ignore_errors:
                print(f"? {description} (error ignored: {e})")
                return True
            else:
                print(f"✗ Error: {description} - {e}")
                return False
    
    def remove_scheduler(self) -> bool:
        """Remove the launchd scheduler"""
        print("Removing scheduled task...")
        
        # Check if job is loaded
        result = subprocess.run([
            'launchctl', 'list', self.plist_name
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Job is loaded, unload it
            if not self.run_command([
                'launchctl', 'unload', str(self.plist_path)
            ], f"Unloading {self.plist_name}"):
                print("? Could not unload job (it may not be running)")
        else:
            print("✓ Scheduler job was not loaded")
        
        # Remove plist file
        if self.plist_path.exists():
            try:
                self.plist_path.unlink()
                print(f"✓ Removed plist file: {self.plist_path}")
            except Exception as e:
                print(f"? Could not remove plist file: {e}")
        else:
            print("✓ Plist file already removed")
        
        return True
    
    def remove_virtual_environment(self) -> bool:
        """Remove the virtual environment"""
        if self.venv_path.exists():
            try:
                shutil.rmtree(self.venv_path)
                print(f"✓ Removed virtual environment: {self.venv_path}")
                return True
            except Exception as e:
                print(f"✗ Could not remove virtual environment: {e}")
                return False
        else:
            print("✓ Virtual environment already removed")
            return True
    
    def remove_data_files(self, keep_reports: bool = False) -> bool:
        """Remove data files and databases"""
        data_dir = self.base_dir / "data"
        cache_dir = self.base_dir / "cache"
        logs_dir = self.base_dir / "logs"
        reports_dir = self.base_dir / "reports"
        
        # Remove data directory
        if data_dir.exists():
            try:
                shutil.rmtree(data_dir)
                print(f"✓ Removed data directory: {data_dir}")
            except Exception as e:
                print(f"? Could not remove data directory: {e}")
        
        # Remove cache directory
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                print(f"✓ Removed cache directory: {cache_dir}")
            except Exception as e:
                print(f"? Could not remove cache directory: {e}")
        
        # Remove logs directory
        if logs_dir.exists():
            try:
                shutil.rmtree(logs_dir)
                print(f"✓ Removed logs directory: {logs_dir}")
            except Exception as e:
                print(f"? Could not remove logs directory: {e}")
        
        # Handle reports directory
        if reports_dir.exists():
            if keep_reports:
                print(f"⚠️  Keeping reports directory: {reports_dir}")
                print("   (contains your generated briefing reports)")
            else:
                try:
                    shutil.rmtree(reports_dir)
                    print(f"✓ Removed reports directory: {reports_dir}")
                except Exception as e:
                    print(f"? Could not remove reports directory: {e}")
        
        return True
    
    def remove_configuration(self) -> bool:
        """Remove configuration files"""
        config_files = [
            self.base_dir / "config.json",
            self.base_dir / ".env"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    config_file.unlink()
                    print(f"✓ Removed configuration: {config_file.name}")
                except Exception as e:
                    print(f"? Could not remove {config_file.name}: {e}")
        
        return True
    
    def remove_templates(self) -> bool:
        """Remove generated template files"""
        templates_dir = self.base_dir / "templates"
        
        if templates_dir.exists():
            try:
                shutil.rmtree(templates_dir)
                print(f"✓ Removed templates directory: {templates_dir}")
            except Exception as e:
                print(f"? Could not remove templates directory: {e}")
        
        return True
    
    def show_remaining_files(self) -> None:
        """Show what files remain after uninstallation"""
        print("\n📁 REMAINING FILES:")
        
        remaining_files = []
        for item in self.base_dir.iterdir():
            if item.name not in ['venv', 'data', 'cache', 'logs', 'templates'] and not item.name.startswith('.'):
                remaining_files.append(item)
        
        if remaining_files:
            print(f"The following files remain in {self.base_dir}:")
            for item in remaining_files:
                if item.is_file():
                    print(f"   📄 {item.name}")
                elif item.is_dir():
                    print(f"   📁 {item.name}/")
            
            print("\nThese are the core system files. To completely remove")
            print("the system, you can delete the entire directory:")
            print(f"   rm -rf {self.base_dir}")
        else:
            print("✓ All system files have been removed")
        
        # Check for reports
        reports_dir = self.base_dir / "reports"
        if reports_dir.exists():
            report_files = list(reports_dir.glob("*.html"))
            if report_files:
                print(f"\n📊 {len(report_files)} report files preserved in:")
                print(f"   {reports_dir}")
    
    def uninstall(self, keep_reports: bool = True, interactive: bool = True) -> bool:
        """Main uninstallation process"""
        print("🗑️  AI Intelligence Briefing System Uninstaller")
        print("=" * 50)
        
        if interactive:
            print("\nThis will remove:")
            print("   • Scheduled daily task")
            print("   • Virtual environment and dependencies")
            print("   • Database and cache files")
            print("   • Log files")
            print("   • Configuration files")
            
            if not keep_reports:
                print("   • Generated report files")
            else:
                print("   ⚠️  Report files will be PRESERVED")
            
            print(f"\nInstallation directory: {self.base_dir}")
            
            response = input("\nContinue with uninstallation? [y/N]: ").strip().lower()
            if response not in ['y', 'yes']:
                print("❌ Uninstallation cancelled")
                return False
        
        total_steps = 6
        
        try:
            # Step 1: Remove Scheduler
            self.print_step(1, total_steps, "Removing scheduled task")
            self.remove_scheduler()
            
            # Step 2: Remove Virtual Environment
            self.print_step(2, total_steps, "Removing virtual environment")
            self.remove_virtual_environment()
            
            # Step 3: Remove Data Files
            self.print_step(3, total_steps, "Removing data files")
            self.remove_data_files(keep_reports=keep_reports)
            
            # Step 4: Remove Configuration
            self.print_step(4, total_steps, "Removing configuration")
            self.remove_configuration()
            
            # Step 5: Remove Templates
            self.print_step(5, total_steps, "Removing templates")
            self.remove_templates()
            
            # Step 6: Complete
            self.print_step(6, total_steps, "Uninstallation complete")
            self.show_remaining_files()
            
            print("\n" + "="*60)
            print("✅ UNINSTALLATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            
            print("\n📋 SUMMARY:")
            print("   • Daily briefing scheduler removed")
            print("   • All system data and cache cleared")
            print("   • Python dependencies removed")
            
            if keep_reports:
                print("   • Report files preserved for your reference")
            
            print("\n🙏 Thank you for using AI Intelligence Briefing!")
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n❌ Uninstallation cancelled by user")
            return False
        except Exception as e:
            print(f"\n\n❌ Uninstallation failed: {e}")
            return False


def main():
    """Main uninstaller entry point"""
    interactive = True
    keep_reports = True
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if "--help" in sys.argv:
            print("AI Intelligence Briefing System Uninstaller")
            print("\nUsage: python uninstall.py [options]")
            print("\nOptions:")
            print("  --help              Show this help message")
            print("  --force             Skip confirmation prompts")
            print("  --remove-reports    Also remove generated reports")
            print("  --keep-reports      Keep generated reports (default)")
            print("\nThis uninstaller will:")
            print("  • Remove the daily scheduler")
            print("  • Remove virtual environment")
            print("  • Remove database and cache files")
            print("  • Remove configuration files")
            print("  • Optionally preserve report files")
            return
        
        if "--force" in sys.argv:
            interactive = False
        
        if "--remove-reports" in sys.argv:
            keep_reports = False
        elif "--keep-reports" in sys.argv:
            keep_reports = True
    
    uninstaller = BriefingUninstaller()
    success = uninstaller.uninstall(keep_reports=keep_reports, interactive=interactive)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()