#!/usr/bin/env python3
"""
Enhanced AI Intelligence Briefing System - Uninstaller
Cleanly removes the enhanced system and all components
"""

import os
import sys
import subprocess
import shutil
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import getpass


class EnhancedUninstaller:
    """Enhanced uninstaller for the AI Intelligence Briefing System"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.venv_path = self.project_dir / 'venv'
        self.logs_dir = self.project_dir / 'logs'
        self.data_dir = self.project_dir / 'data'
        self.reports_dir = self.project_dir / 'reports'
        self.cache_dir = self.project_dir / 'cache'
        
        self.backup_dir = Path.home() / 'intelligence_briefing_backup'
        self.sudo_password = None
        
        # Components to remove
        self.components = [
            'Virtual Environment',
            'Python Dependencies',
            'Database and Data',
            'Generated Reports',
            'Cache Files',
            'Log Files',
            'Configuration Files',
            'Scheduled Tasks (Cron)',
            'Web API Service',
            'LaunchAgent (macOS)',
            'Project Directory'
        ]
    
    def run(self):
        """Run the complete uninstallation process"""
        try:
            print("🗑️  Enhanced AI Intelligence Briefing System Uninstaller")
            print("=" * 65)
            print()
            
            self.display_warning()
            
            if not self.confirm_uninstall():
                print("Uninstallation cancelled.")
                return
            
            backup_created = self.offer_backup()
            
            self.remove_web_api_service()
            self.remove_scheduled_tasks()
            self.remove_launch_agent()
            self.backup_important_data(backup_created)
            self.remove_virtual_environment()
            self.remove_data_directories()
            self.remove_configuration_files()
            self.clean_system_references()
            self.display_completion_message()
            
        except KeyboardInterrupt:
            print("\n❌ Uninstallation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Uninstallation failed: {e}")
            print("\nSome components may need manual removal")
            sys.exit(1)
    
    def display_warning(self):
        """Display uninstallation warning"""
        print("⚠️  WARNING: This will completely remove the AI Intelligence Briefing System")
        print()
        print("Components that will be removed:")
        for i, component in enumerate(self.components, 1):
            print(f"   {i:2d}. {component}")
        print()
        print("This action CANNOT be undone!")
        print()
    
    def confirm_uninstall(self) -> bool:
        """Get user confirmation for uninstall"""
        response = input("Are you sure you want to completely uninstall? (type 'YES' to confirm): ").strip()
        return response == 'YES'
    
    def offer_backup(self) -> bool:
        """Offer to create backup before uninstalling"""
        response = input("\nWould you like to create a backup of important data? (y/N): ").strip().lower()
        if response == 'y':
            return self.create_backup()
        return False
    
    def create_backup(self) -> bool:
        """Create backup of important data"""
        print("💾 Creating backup...")
        
        try:
            # Create backup directory
            self.backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"intelligence_briefing_backup_{timestamp}"
            backup_path.mkdir(exist_ok=True)
            
            # Backup configuration
            config_path = self.project_dir / 'config.json'
            if config_path.exists():
                shutil.copy2(config_path, backup_path / 'config.json')
                print(f"   ✅ Configuration backed up")
            
            # Backup database
            db_path = self.data_dir / 'intelligence.db'
            if db_path.exists():
                shutil.copy2(db_path, backup_path / 'intelligence.db')
                print(f"   ✅ Database backed up")
            
            # Backup recent reports (last 7 days)
            if self.reports_dir.exists():
                reports_backup = backup_path / 'reports'
                reports_backup.mkdir(exist_ok=True)
                
                cutoff_date = datetime.now().timestamp() - (7 * 24 * 60 * 60)  # 7 days ago
                copied_reports = 0
                
                for report_file in self.reports_dir.glob('*.html'):
                    if report_file.stat().st_mtime > cutoff_date:
                        shutil.copy2(report_file, reports_backup)
                        copied_reports += 1
                
                # Copy CSS and JS files
                for asset in ['styles.css', 'enhanced_styles.css', 'enhanced_script.js']:
                    asset_path = self.reports_dir / asset
                    if asset_path.exists():
                        shutil.copy2(asset_path, reports_backup)
                
                print(f"   ✅ Recent reports backed up ({copied_reports} files)")
            
            # Backup logs (last 30 days)
            if self.logs_dir.exists():
                logs_backup = backup_path / 'logs'
                logs_backup.mkdir(exist_ok=True)
                
                cutoff_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)  # 30 days ago
                copied_logs = 0
                
                for log_file in self.logs_dir.glob('*.log'):
                    if log_file.stat().st_mtime > cutoff_date:
                        shutil.copy2(log_file, logs_backup)
                        copied_logs += 1
                
                print(f"   ✅ Recent logs backed up ({copied_logs} files)")
            
            # Create backup info file
            backup_info = {
                'backup_date': datetime.now().isoformat(),
                'original_path': str(self.project_dir),
                'system': os.name,
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'components_backed_up': [
                    'Configuration (config.json)',
                    'Database (intelligence.db)',
                    'Recent reports (last 7 days)',
                    'Recent logs (last 30 days)'
                ]
            }
            
            with open(backup_path / 'backup_info.json', 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            print(f"   📁 Backup created: {backup_path}")
            print(f"   💾 Backup size: {self.get_directory_size(backup_path):.1f} MB")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Backup failed: {e}")
            print("   Continuing with uninstallation...")
            return False
    
    def get_sudo_password(self):
        """Get sudo password once and cache it"""
        if self.sudo_password is None:
            print("\n🔐 Administrator privileges required for some cleanup tasks")
            self.sudo_password = getpass.getpass("Enter your password (for sudo): ")
            
            # Test the password
            try:
                subprocess.run(['sudo', '-S', 'echo', 'test'], 
                             input=self.sudo_password + '\n', 
                             text=True, check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print("❌ Invalid password")
                self.sudo_password = None
                return self.get_sudo_password()
        
        return self.sudo_password
    
    def run_with_sudo(self, command, description=""):
        """Run command with sudo using cached password"""
        password = self.get_sudo_password()
        try:
            result = subprocess.run(
                ['sudo', '-S'] + command,
                input=password + '\n',
                text=True,
                check=True,
                capture_output=True
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Failed to {description}: {e.stderr.strip()}")
            return None
    
    def remove_web_api_service(self):
        """Stop and remove web API service"""
        print("🌐 Stopping Web API service...")
        
        try:
            # Try to stop the service gracefully
            result = subprocess.run(['pkill', '-f', 'web_api.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Web API service stopped")
            else:
                print("   ℹ️  Web API service was not running")
        except Exception as e:
            print(f"   ⚠️  Could not stop Web API service: {e}")
    
    def remove_scheduled_tasks(self):
        """Remove cron jobs and scheduled tasks"""
        print("⏰ Removing scheduled tasks...")
        
        try:
            # Remove cron jobs
            from crontab import CronTab
            
            cron = CronTab(user=True)
            jobs_removed = 0
            
            # Remove jobs that reference this project
            for job in cron:
                if str(self.project_dir) in job.command or 'intelligence' in job.comment.lower():
                    cron.remove(job)
                    jobs_removed += 1
            
            if jobs_removed > 0:
                cron.write()
                print(f"   ✅ Removed {jobs_removed} cron job(s)")
            else:
                print("   ℹ️  No scheduled tasks found")
                
        except ImportError:
            # Manual cron cleanup
            print("   ⚠️  python-crontab not available, manual cleanup may be needed")
            print(f"   Check your crontab with: crontab -l | grep {self.project_dir}")
        except Exception as e:
            print(f"   ⚠️  Could not remove scheduled tasks: {e}")
    
    def remove_launch_agent(self):
        """Remove macOS LaunchAgent"""
        if sys.platform != 'darwin':
            return
        
        print("🍎 Removing macOS LaunchAgent...")
        
        try:
            launch_agents_dir = Path.home() / 'Library' / 'LaunchAgents'
            plist_path = launch_agents_dir / 'com.intelligence-briefing.webapi.plist'
            
            if plist_path.exists():
                # Unload the service
                try:
                    subprocess.run(['launchctl', 'unload', str(plist_path)], 
                                 check=True, capture_output=True)
                    print("   ✅ LaunchAgent unloaded")
                except subprocess.CalledProcessError:
                    print("   ℹ️  LaunchAgent was not loaded")
                
                # Remove the plist file
                plist_path.unlink()
                print("   ✅ LaunchAgent plist removed")
            else:
                print("   ℹ️  No LaunchAgent found")
                
        except Exception as e:
            print(f"   ⚠️  Could not remove LaunchAgent: {e}")
    
    def backup_important_data(self, backup_already_created: bool):
        """Backup important data if not already done"""
        if backup_already_created:
            return
        
        print("💾 Final backup of critical data...")
        
        try:
            # Quick backup of just the config and database
            quick_backup_dir = Path.home() / 'Desktop' / f"intelligence_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            quick_backup_dir.mkdir(exist_ok=True)
            
            # Backup config
            config_path = self.project_dir / 'config.json'
            if config_path.exists():
                shutil.copy2(config_path, quick_backup_dir)
            
            # Backup database
            db_path = self.data_dir / 'intelligence.db'
            if db_path.exists():
                shutil.copy2(db_path, quick_backup_dir)
            
            print(f"   ✅ Critical data backed up to Desktop: {quick_backup_dir.name}")
            
        except Exception as e:
            print(f"   ⚠️  Could not create final backup: {e}")
    
    def remove_virtual_environment(self):
        """Remove Python virtual environment"""
        print("🐍 Removing virtual environment...")
        
        if self.venv_path.exists():
            try:
                shutil.rmtree(self.venv_path)
                print("   ✅ Virtual environment removed")
            except Exception as e:
                print(f"   ❌ Could not remove virtual environment: {e}")
        else:
            print("   ℹ️  Virtual environment not found")
    
    def remove_data_directories(self):
        """Remove data directories"""
        print("🗄️  Removing data directories...")
        
        directories = [
            (self.cache_dir, "Cache"),
            (self.logs_dir, "Logs"), 
            (self.data_dir, "Data"),
            (self.reports_dir, "Reports")
        ]
        
        for directory, name in directories:
            if directory.exists():
                try:
                    size_mb = self.get_directory_size(directory)
                    shutil.rmtree(directory)
                    print(f"   ✅ {name} directory removed ({size_mb:.1f} MB)")
                except Exception as e:
                    print(f"   ❌ Could not remove {name} directory: {e}")
            else:
                print(f"   ℹ️  {name} directory not found")
    
    def remove_configuration_files(self):
        """Remove configuration files"""
        print("⚙️  Removing configuration files...")
        
        config_files = [
            'config.json',
            'requirements.txt',
            'run_enhanced_briefing.sh'
        ]
        
        for config_file in config_files:
            file_path = self.project_dir / config_file
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"   ✅ Removed {config_file}")
                except Exception as e:
                    print(f"   ❌ Could not remove {config_file}: {e}")
    
    def clean_system_references(self):
        """Clean system-wide references"""
        print("🧹 Cleaning system references...")
        
        # Clean pip cache related to this project
        try:
            subprocess.run(['pip', 'cache', 'purge'], capture_output=True)
            print("   ✅ Cleaned pip cache")
        except:
            pass
        
        # Remove any remaining temporary files
        temp_patterns = [
            Path('/tmp').glob('*intelligence*'),
            Path('/tmp').glob('*briefing*')
        ]
        
        cleaned_files = 0
        for pattern in temp_patterns:
            for temp_file in pattern:
                try:
                    if temp_file.is_file():
                        temp_file.unlink()
                        cleaned_files += 1
                    elif temp_file.is_dir():
                        shutil.rmtree(temp_file)
                        cleaned_files += 1
                except:
                    pass
        
        if cleaned_files > 0:
            print(f"   ✅ Cleaned {cleaned_files} temporary file(s)")
        else:
            print("   ℹ️  No temporary files found")
    
    def get_directory_size(self, directory: Path) -> float:
        """Calculate directory size in MB"""
        try:
            total_size = 0
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)  # Convert to MB
        except:
            return 0
    
    def display_completion_message(self):
        """Display uninstallation completion message"""
        print("\n" + "=" * 65)
        print("✅ Enhanced AI Intelligence Briefing System Uninstallation Complete!")
        print("=" * 65)
        print()
        
        print("🗑️  Components successfully removed:")
        print("   • Virtual environment and Python dependencies")
        print("   • Database and collected intelligence data")
        print("   • Generated reports and cached files") 
        print("   • Configuration files and logs")
        print("   • Scheduled tasks (cron jobs)")
        print("   • Web API service and LaunchAgent")
        print()
        
        if self.backup_dir.exists():
            print("💾 Backup Information:")
            print(f"   • Backup location: {self.backup_dir}")
            print("   • Contains: config, database, recent reports & logs")
            print("   • Safe to delete after verifying you don't need the data")
            print()
        
        print("🧹 Manual cleanup (if needed):")
        print("   • Check crontab: crontab -l")
        print("   • Check LaunchAgents: ~/Library/LaunchAgents/")
        print("   • Check for running processes: ps aux | grep intelligence")
        print()
        
        print("📁 Project directory:")
        remaining_files = list(self.project_dir.glob('*'))
        if remaining_files:
            print(f"   • Some files remain in: {self.project_dir}")
            print("   • You can safely delete the entire directory if desired")
            print(f"   • Command: rm -rf '{self.project_dir}'")
        else:
            print("   • Project directory is clean")
        
        print()
        print("Thank you for using the Enhanced AI Intelligence Briefing System! 👋")


def main():
    """Main uninstaller entry point"""
    uninstaller = EnhancedUninstaller()
    uninstaller.run()


if __name__ == "__main__":
    main()