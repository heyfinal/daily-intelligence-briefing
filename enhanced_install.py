#!/usr/bin/env python3
"""
Enhanced AI Intelligence Briefing System - Installer
Installs the enhanced system with all new features
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
import plistlib
import tempfile


class EnhancedInstaller:
    """Enhanced installer for the AI Intelligence Briefing System"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.venv_path = self.project_dir / 'venv'
        self.python_exec = self.venv_path / 'bin' / 'python'
        self.pip_exec = self.venv_path / 'bin' / 'pip'
        self.logs_dir = self.project_dir / 'logs'
        self.data_dir = self.project_dir / 'data'
        self.reports_dir = self.project_dir / 'reports'
        self.cache_dir = self.project_dir / 'cache'
        
        # Enhanced requirements
        self.requirements = [
            'requests>=2.31.0',
            'feedparser>=6.0.10',
            'praw>=7.7.1',
            'aiohttp>=3.8.6',
            'beautifulsoup4>=4.12.2',
            'python-dateutil>=2.8.2',
            'jinja2>=3.1.2',
            'schedule>=1.2.0',
            'flask>=2.3.3',
            'flask-cors>=4.0.0',
            'python-crontab>=3.0.0',
            'gitpython>=3.1.40',
            'psutil>=5.9.6',
            'click>=8.1.7',
            'rich>=13.6.0',
            'pydantic>=2.4.2',
            'asyncio-throttle>=1.0.2'
        ]
        
        self.config_template = {
            "github_token": "",
            "reddit_client_id": "",
            "reddit_client_secret": "",
            "report_generation_time": "04:30",
            "report_ready_time": "05:00",
            "timezone": "America/New_York",
            "auto_open_browser": True,
            "max_items_per_category": 10,
            "enhanced_features": {
                "project_scanning": True,
                "installation_management": True,
                "system_health_monitoring": True,
                "web_api": True,
                "api_port": 5000
            },
            "security": {
                "allowed_package_managers": ["brew", "npm", "pip", "cargo", "go"],
                "require_confirmation": True,
                "log_all_commands": True
            }
        }
        
        self.sudo_password = None
    
    def run(self):
        """Run the complete installation process"""
        try:
            print("🚀 Enhanced AI Intelligence Briefing System Installer")
            print("=" * 60)
            print()
            
            self.check_system_requirements()
            self.setup_directories()
            self.setup_virtual_environment()
            self.install_python_dependencies()
            self.setup_configuration()
            self.initialize_database()
            self.setup_scheduling()
            self.setup_web_api_service()
            self.run_initial_tests()
            self.display_completion_message()
            
        except KeyboardInterrupt:
            print("\n❌ Installation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Installation failed: {e}")
            print("\nRun with --debug for more details")
            sys.exit(1)
    
    def check_system_requirements(self):
        """Check system requirements"""
        print("🔍 Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            raise Exception("Python 3.8 or higher is required")
        
        # Check operating system
        if sys.platform not in ['darwin', 'linux']:
            print("⚠️  Warning: This system is designed for macOS and Linux")
        
        # Check for required system tools
        required_tools = ['git', 'curl', 'crontab']
        missing_tools = []
        
        for tool in required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"❌ Missing required tools: {', '.join(missing_tools)}")
            if sys.platform == 'darwin':
                print("Install using: brew install " + ' '.join(missing_tools))
            else:
                print("Install using your package manager")
            sys.exit(1)
        
        # Check available disk space
        disk_usage = shutil.disk_usage(self.project_dir)
        free_gb = disk_usage.free / (1024 ** 3)
        if free_gb < 1:
            print("⚠️  Warning: Less than 1GB free disk space available")
        
        print("✅ System requirements check passed")
    
    def get_sudo_password(self):
        """Get sudo password once and cache it"""
        if self.sudo_password is None:
            print("\n🔐 Some installation steps require administrator privileges")
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
            raise Exception(f"Failed to execute {description}: {e.stderr}")
    
    def setup_directories(self):
        """Setup project directories"""
        print("📁 Setting up project directories...")
        
        directories = [
            self.logs_dir,
            self.data_dir,
            self.reports_dir,
            self.cache_dir,
            self.project_dir / 'src',
            self.project_dir / 'templates'
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            print(f"   Created: {directory}")
        
        # Set appropriate permissions
        for directory in directories:
            os.chmod(directory, 0o755)
        
        print("✅ Project directories setup complete")
    
    def setup_virtual_environment(self):
        """Setup Python virtual environment"""
        print("🐍 Setting up Python virtual environment...")
        
        if self.venv_path.exists():
            print("   Virtual environment already exists, removing...")
            shutil.rmtree(self.venv_path)
        
        # Create virtual environment
        subprocess.run([sys.executable, '-m', 'venv', str(self.venv_path)], check=True)
        
        # Upgrade pip in virtual environment
        subprocess.run([str(self.pip_exec), 'install', '--upgrade', 'pip'], check=True)
        
        print("✅ Virtual environment setup complete")
    
    def install_python_dependencies(self):
        """Install Python dependencies"""
        print("📦 Installing Python dependencies...")
        
        # Create requirements.txt
        requirements_path = self.project_dir / 'requirements.txt'
        with open(requirements_path, 'w') as f:
            f.write('\n'.join(self.requirements))
        
        # Install requirements
        subprocess.run([
            str(self.pip_exec), 'install', '-r', str(requirements_path)
        ], check=True)
        
        print("✅ Python dependencies installed")
    
    def setup_configuration(self):
        """Setup configuration files"""
        print("⚙️  Setting up configuration...")
        
        config_path = self.project_dir / 'config.json'
        
        if config_path.exists():
            print("   Configuration file already exists")
            # Merge with existing config
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
            
            # Add enhanced features if not present
            if 'enhanced_features' not in existing_config:
                existing_config['enhanced_features'] = self.config_template['enhanced_features']
            if 'security' not in existing_config:
                existing_config['security'] = self.config_template['security']
            
            with open(config_path, 'w') as f:
                json.dump(existing_config, f, indent=2)
        else:
            with open(config_path, 'w') as f:
                json.dump(self.config_template, f, indent=2)
        
        print(f"   Configuration saved to: {config_path}")
        print("   ⚠️  Remember to update GitHub and Reddit API credentials")
        
        print("✅ Configuration setup complete")
    
    def initialize_database(self):
        """Initialize SQLite database"""
        print("🗄️  Initializing database...")
        
        db_path = self.data_dir / 'intelligence.db'
        
        # Create database schema
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Enhanced database schema
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS updates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    content TEXT,
                    source TEXT NOT NULL,
                    category TEXT,
                    published_date DATETIME NOT NULL,
                    collected_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    importance_score REAL DEFAULT 0,
                    metadata TEXT,
                    processed BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date DATE NOT NULL UNIQUE,
                    file_path TEXT NOT NULL,
                    total_updates INTEGER DEFAULT 0,
                    metadata TEXT,
                    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Enhanced tables for new features
                CREATE TABLE IF NOT EXISTS installations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL,
                    package_name TEXT NOT NULL,
                    package_manager TEXT NOT NULL,
                    command TEXT NOT NULL,
                    status TEXT NOT NULL, -- queued, installing, completed, failed
                    started_at DATETIME,
                    completed_at DATETIME,
                    output TEXT,
                    error TEXT,
                    installed_version TEXT
                );
                
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    health_score INTEGER NOT NULL,
                    last_scanned DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                );
                
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    overall_health TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    recommendations TEXT
                );
                
                -- Create indexes for better performance
                CREATE INDEX IF NOT EXISTS idx_updates_date ON updates(published_date);
                CREATE INDEX IF NOT EXISTS idx_updates_source ON updates(source);
                CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at);
                CREATE INDEX IF NOT EXISTS idx_installations_batch ON installations(batch_id);
                CREATE INDEX IF NOT EXISTS idx_projects_health ON projects(health_score);
            ''')
            
            conn.commit()
        
        print(f"   Database initialized: {db_path}")
        print("✅ Database initialization complete")
    
    def setup_scheduling(self):
        """Setup automated scheduling"""
        print("⏰ Setting up automated scheduling...")
        
        # Create launcher script
        launcher_script = self.project_dir / 'run_enhanced_briefing.sh'
        launcher_content = f'''#!/bin/bash
cd "{self.project_dir}"
source venv/bin/activate
python run_briefing.py --enhanced
'''
        
        with open(launcher_script, 'w') as f:
            f.write(launcher_content)
        
        os.chmod(launcher_script, 0o755)
        
        # Setup cron job for daily execution at 5 AM
        try:
            from crontab import CronTab
            
            # Get current user's crontab
            cron = CronTab(user=True)
            
            # Remove existing jobs for this project
            cron.remove_all(command=str(launcher_script))
            
            # Add new job
            job = cron.new(command=str(launcher_script))
            job.setall('0 5 * * *')  # Daily at 5 AM
            job.set_comment('Enhanced AI Intelligence Briefing')
            
            cron.write()
            
            print("   Cron job scheduled: Daily at 5:00 AM")
            
        except ImportError:
            print("   ⚠️  python-crontab not available, manual cron setup required")
            print(f"   Add this to your crontab: 0 5 * * * {launcher_script}")
        
        print("✅ Scheduling setup complete")
    
    def setup_web_api_service(self):
        """Setup web API as a system service (macOS)"""
        if sys.platform != 'darwin':
            print("⚠️  Web API service setup only available on macOS")
            return
        
        print("🌐 Setting up Web API service...")
        
        # Create plist for LaunchAgent
        plist_content = {
            'Label': 'com.intelligence-briefing.webapi',
            'ProgramArguments': [
                str(self.python_exec),
                str(self.project_dir / 'src' / 'web_api.py')
            ],
            'WorkingDirectory': str(self.project_dir),
            'RunAtLoad': True,
            'KeepAlive': True,
            'StandardOutPath': str(self.logs_dir / 'webapi.log'),
            'StandardErrorPath': str(self.logs_dir / 'webapi_error.log'),
            'EnvironmentVariables': {
                'PATH': f"{self.venv_path / 'bin'}:/usr/local/bin:/usr/bin:/bin"
            }
        }
        
        # Save to LaunchAgents directory
        launch_agents_dir = Path.home() / 'Library' / 'LaunchAgents'
        launch_agents_dir.mkdir(exist_ok=True)
        
        plist_path = launch_agents_dir / 'com.intelligence-briefing.webapi.plist'
        
        with open(plist_path, 'wb') as f:
            plistlib.dump(plist_content, f)
        
        try:
            # Load the service
            subprocess.run(['launchctl', 'load', str(plist_path)], check=True)
            print(f"   Web API service loaded: {plist_path}")
            print("   API will be available at: http://127.0.0.1:5000/api/")
        except subprocess.CalledProcessError:
            print("   ⚠️  Could not load web API service automatically")
            print(f"   Manual load: launchctl load {plist_path}")
        
        print("✅ Web API service setup complete")
    
    def run_initial_tests(self):
        """Run initial system tests"""
        print("🧪 Running initial tests...")
        
        try:
            # Test database connection
            db_path = self.data_dir / 'intelligence.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM updates')
                print("   ✅ Database connection test passed")
            
            # Test enhanced modules import
            test_script = f'''
import sys
sys.path.insert(0, "{self.project_dir / 'src'}")

try:
    from project_scanner import ProjectScanner
    from installation_manager import InstallationManager
    from enhanced_html_generator import EnhancedHTMLGenerator
    from web_api import WebAPI
    print("✅ All enhanced modules imported successfully")
except ImportError as e:
    print(f"❌ Module import failed: {{e}}")
    sys.exit(1)
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_script)
                temp_script = f.name
            
            try:
                subprocess.run([str(self.python_exec), temp_script], check=True, capture_output=True)
                print("   ✅ Enhanced modules test passed")
            finally:
                os.unlink(temp_script)
            
            # Test configuration loading
            config_path = self.project_dir / 'config.json'
            with open(config_path, 'r') as f:
                config = json.load(f)
                if 'enhanced_features' in config:
                    print("   ✅ Enhanced configuration test passed")
                else:
                    print("   ⚠️  Enhanced configuration not found")
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            print("   System may still work, but please check logs")
        
        print("✅ Initial tests complete")
    
    def display_completion_message(self):
        """Display installation completion message"""
        print("\n" + "=" * 60)
        print("🎉 Enhanced AI Intelligence Briefing System Installation Complete!")
        print("=" * 60)
        print()
        
        print("📋 What was installed:")
        print("   • Enhanced HTML reports with project dashboard")
        print("   • Local project scanner and health analyzer")
        print("   • Interactive installation management system")
        print("   • Web API for real-time interactions")
        print("   • System health monitoring and recommendations")
        print("   • Automated daily scheduling")
        print("   • Comprehensive security and validation")
        print()
        
        print("🚀 Quick Start:")
        print(f"   1. Update API credentials in: {self.project_dir}/config.json")
        print(f"   2. Run manual test: {self.python_exec} run_briefing.py --enhanced")
        print("   3. Access web dashboard: http://127.0.0.1:5000/api/")
        print("   4. View latest report in the 'reports' directory")
        print()
        
        print("📖 Key Features:")
        print("   • Daily at 5 AM: Automated report generation")
        print("   • Real-time: Project health monitoring")
        print("   • One-click: Package installation from intelligence data")
        print("   • AI-powered: Smart recommendations for projects")
        print("   • Secure: Validated installation commands")
        print()
        
        print("🔧 Commands:")
        print(f"   • Manual run:      {self.python_exec} run_briefing.py --enhanced")
        print(f"   • Check status:    {self.python_exec} run_briefing.py --status")
        print(f"   • Start web API:   {self.python_exec} src/web_api.py")
        print(f"   • Uninstall:       {self.python_exec} enhanced_uninstall.py")
        print()
        
        print("📁 Important Directories:")
        print(f"   • Reports:         {self.reports_dir}")
        print(f"   • Logs:           {self.logs_dir}")
        print(f"   • Database:       {self.data_dir}/intelligence.db")
        print(f"   • Configuration:  {self.project_dir}/config.json")
        print()
        
        print("⚠️  Remember to:")
        print("   • Add GitHub personal access token to config.json")
        print("   • Add Reddit API credentials if using Reddit sources")
        print("   • Check firewall settings for web API (port 5000)")
        print()
        
        print("Happy Intelligence Gathering! 🤖📰")


def main():
    """Main installer entry point"""
    installer = EnhancedInstaller()
    installer.run()


if __name__ == "__main__":
    main()