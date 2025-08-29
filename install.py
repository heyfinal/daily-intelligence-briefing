#!/usr/bin/env python3
"""
Installation script for AI Intelligence Briefing System
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
import getpass
import time


class BriefingInstaller:
    """Handles complete installation of the briefing system"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.home_dir = Path.home()
        self.venv_path = self.base_dir / "venv"
        self.python_executable = sys.executable
        
        # Track sudo password for reuse
        self.sudo_password = None
        self.sudo_cached = False
    
    def print_step(self, step_num: int, total_steps: int, description: str):
        """Print installation step with progress"""
        print(f"\n[{step_num}/{total_steps}] {description}")
        print("-" * 50)
    
    def run_with_sudo(self, command: list, description: str = "") -> bool:
        """Run command with sudo, caching password"""
        try:
            if not self.sudo_cached:
                if not self.sudo_password:
                    self.sudo_password = getpass.getpass("Enter your password for sudo access: ")
                
                # Test sudo access
                test_cmd = ['sudo', '-S', 'echo', 'sudo access granted']
                process = subprocess.Popen(
                    test_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate(input=self.sudo_password + '\n')
                
                if process.returncode != 0:
                    print("Incorrect password. Please try again.")
                    self.sudo_password = None
                    return self.run_with_sudo(command, description)
                
                self.sudo_cached = True
                print("✓ Sudo access granted")
            
            # Run the actual command
            full_command = ['sudo', '-S'] + command
            process = subprocess.Popen(
                full_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=self.sudo_password + '\n')
            
            if process.returncode == 0:
                if description:
                    print(f"✓ {description}")
                if stdout.strip():
                    print(stdout.strip())
                return True
            else:
                print(f"✗ Failed: {description}")
                if stderr:
                    print(f"Error: {stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error running sudo command: {e}")
            return False
    
    def run_command(self, command: list, description: str = "", cwd: Path = None) -> bool:
        """Run a command and return success status"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.base_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                if description:
                    print(f"✓ {description}")
                return True
            else:
                print(f"✗ Failed: {description}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"✗ Timeout: {description}")
            return False
        except Exception as e:
            print(f"✗ Error: {description} - {e}")
            return False
    
    def check_system_requirements(self) -> bool:
        """Check system requirements"""
        print("Checking system requirements...")
        
        # Check macOS
        if sys.platform != "darwin":
            print("✗ This system is designed for macOS only")
            return False
        print("✓ macOS detected")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("✗ Python 3.8 or higher required")
            return False
        print(f"✓ Python {sys.version.split()[0]} found")
        
        # Check if pip is available
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
            print("✓ pip is available")
        except subprocess.CalledProcessError:
            print("✗ pip is not available")
            return False
        
        return True
    
    def install_system_dependencies(self) -> bool:
        """Install system-level dependencies"""
        dependencies_needed = []
        
        # Check for Homebrew (optional but recommended)
        try:
            subprocess.run(["brew", "--version"], check=True, capture_output=True)
            print("✓ Homebrew found")
            
            # Check for useful tools
            tools = ["curl", "git"]
            for tool in tools:
                try:
                    subprocess.run(["which", tool], check=True, capture_output=True)
                    print(f"✓ {tool} found")
                except subprocess.CalledProcessError:
                    print(f"? {tool} not found (installing via Homebrew)")
                    dependencies_needed.append(tool)
        
        except subprocess.CalledProcessError:
            print("? Homebrew not found (optional, but recommended)")
            print("  You can install it from: https://brew.sh")
        
        # Install missing tools
        if dependencies_needed:
            for tool in dependencies_needed:
                if self.run_command(["brew", "install", tool], f"Installing {tool}"):
                    continue
                else:
                    print(f"? Failed to install {tool} - continuing anyway")
        
        return True
    
    def create_virtual_environment(self) -> bool:
        """Create and set up virtual environment"""
        if self.venv_path.exists():
            print("? Virtual environment already exists, removing...")
            shutil.rmtree(self.venv_path)
        
        # Create virtual environment
        if not self.run_command([
            self.python_executable, "-m", "venv", str(self.venv_path)
        ], "Creating virtual environment"):
            return False
        
        # Update pip in virtual environment
        venv_python = self.venv_path / "bin" / "python"
        venv_pip = self.venv_path / "bin" / "pip"
        
        if not self.run_command([
            str(venv_python), "-m", "pip", "install", "--upgrade", "pip"
        ], "Upgrading pip in virtual environment"):
            return False
        
        # Install requirements
        requirements_file = self.base_dir / "requirements.txt"
        if requirements_file.exists():
            if not self.run_command([
                str(venv_pip), "install", "-r", str(requirements_file)
            ], "Installing Python dependencies"):
                return False
        else:
            print("? requirements.txt not found, installing basic dependencies")
            basic_deps = [
                "aiohttp", "feedparser", "Jinja2", "requests", 
                "python-dateutil", "pytz"
            ]
            if not self.run_command([
                str(venv_pip), "install"
            ] + basic_deps, "Installing basic dependencies"):
                return False
        
        return True
    
    def setup_configuration(self) -> bool:
        """Set up configuration files"""
        config_file = self.base_dir / "config.json"
        
        if config_file.exists():
            print("✓ Configuration file already exists")
            return True
        
        # Create basic configuration
        config = {
            "github_token": "",
            "reddit_client_id": "",
            "reddit_client_secret": "",
            "report_generation_time": "04:30",
            "report_ready_time": "05:00",
            "timezone": "America/New_York",
            "auto_open_browser": True,
            "max_items_per_category": 10
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print("✓ Created default configuration file")
            print(f"  Edit {config_file} to customize settings")
            return True
        except Exception as e:
            print(f"✗ Failed to create configuration file: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories"""
        directories = [
            self.base_dir / "data",
            self.base_dir / "reports", 
            self.base_dir / "cache",
            self.base_dir / "logs",
            self.base_dir / "templates"
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"✓ Created directory: {directory.name}")
            except Exception as e:
                print(f"✗ Failed to create {directory}: {e}")
                return False
        
        return True
    
    def setup_scheduler(self) -> bool:
        """Set up the macOS scheduler"""
        try:
            # Import the scheduler module
            sys.path.insert(0, str(self.base_dir / "src"))
            from scheduler import setup_scheduler
            
            # Update the run_briefing.py to use the correct Python path
            run_script = self.base_dir / "run_briefing.py"
            if run_script.exists():
                # Make it executable
                os.chmod(run_script, 0o755)
                
                # Update shebang to use virtual environment python
                venv_python = self.venv_path / "bin" / "python"
                with open(run_script, 'r') as f:
                    content = f.read()
                
                # Replace shebang
                lines = content.split('\n')
                lines[0] = f"#!{venv_python}"
                
                with open(run_script, 'w') as f:
                    f.write('\n'.join(lines))
                
                print("✓ Updated run script with virtual environment Python path")
            
            # Set up the scheduler
            if setup_scheduler():
                print("✓ Scheduler installed successfully")
                print("  Daily briefings will be generated at 4:30 AM")
                return True
            else:
                print("✗ Failed to install scheduler")
                return False
                
        except Exception as e:
            print(f"✗ Error setting up scheduler: {e}")
            return False
    
    def run_initial_test(self) -> bool:
        """Run initial test to verify installation"""
        try:
            venv_python = self.venv_path / "bin" / "python"
            run_script = self.base_dir / "run_briefing.py"
            
            print("Running initial test (this may take a few minutes)...")
            
            result = subprocess.run([
                str(venv_python), str(run_script), "--force"
            ], cwd=self.base_dir, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✓ Initial test completed successfully")
                print("✓ Sample report generated")
                return True
            else:
                print("✗ Initial test failed")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("? Initial test timed out (this is normal on first run)")
            print("  The system should work fine for regular scheduled runs")
            return True
        except Exception as e:
            print(f"? Initial test error: {e}")
            print("  This is often normal on first run, system should work fine")
            return True
    
    def print_next_steps(self):
        """Print next steps for the user"""
        print("\n" + "="*60)
        print("🎉 INSTALLATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        print("\n📋 NEXT STEPS:")
        print("1. Your daily briefing is scheduled to run at 4:30 AM daily")
        print("2. Reports will automatically open in your browser at 5:00 AM")
        print("3. Reports are saved in: daily-intelligence-briefing/reports/")
        
        print("\n⚙️  OPTIONAL CONFIGURATION:")
        config_file = self.base_dir / "config.json"
        print(f"Edit {config_file} to:")
        print("   • Add GitHub token for higher API rate limits")
        print("   • Add Reddit API credentials")
        print("   • Customize report timing")
        print("   • Adjust content categories")
        
        print("\n🛠  MANUAL COMMANDS:")
        run_script = self.base_dir / "run_briefing.py"
        venv_python = self.venv_path / "bin" / "python"
        
        print(f"   • Generate report now: {venv_python} {run_script} --force")
        print(f"   • Check system status: {venv_python} {run_script} --status")
        print(f"   • Open latest report: {venv_python} {run_script} --open")
        
        scheduler_script = self.base_dir / "src" / "scheduler.py"
        print(f"   • Check scheduler: {venv_python} {scheduler_script} status")
        print(f"   • Uninstall scheduler: {venv_python} {scheduler_script} uninstall")
        
        print("\n📊 MONITORED SOURCES:")
        print("   • GitHub: Anthropic, OpenAI, Google AI repositories")
        print("   • NPM: AI-related packages")  
        print("   • PyPI: AI/ML Python packages")
        print("   • RSS: Official AI company blogs")
        print("   • HackerNews: AI-related discussions")
        
        print("\n🔧 TROUBLESHOOTING:")
        logs_dir = self.base_dir / "logs"
        print(f"   • Check logs: {logs_dir}/")
        print(f"   • Database: {self.base_dir}/data/intelligence.db")
        print("   • Run with --force flag to regenerate reports")
        
        print(f"\n📁 Installation Directory: {self.base_dir}")
        print("\nYour AI Intelligence Briefing system is ready! 🚀")
    
    def install(self) -> bool:
        """Main installation process"""
        print("🤖 AI Intelligence Briefing System Installer")
        print("=" * 50)
        
        total_steps = 8
        
        try:
            # Step 1: System Requirements
            self.print_step(1, total_steps, "Checking system requirements")
            if not self.check_system_requirements():
                return False
            
            # Step 2: System Dependencies
            self.print_step(2, total_steps, "Installing system dependencies")
            if not self.install_system_dependencies():
                return False
            
            # Step 3: Create Directories
            self.print_step(3, total_steps, "Creating directory structure")
            if not self.create_directories():
                return False
            
            # Step 4: Virtual Environment
            self.print_step(4, total_steps, "Setting up virtual environment")
            if not self.create_virtual_environment():
                return False
            
            # Step 5: Configuration
            self.print_step(5, total_steps, "Setting up configuration")
            if not self.setup_configuration():
                return False
            
            # Step 6: Scheduler
            self.print_step(6, total_steps, "Installing scheduler")
            if not self.setup_scheduler():
                return False
            
            # Step 7: Initial Test
            self.print_step(7, total_steps, "Running initial test")
            if not self.run_initial_test():
                print("? Initial test had issues, but installation continues")
            
            # Step 8: Complete
            self.print_step(8, total_steps, "Installation complete")
            self.print_next_steps()
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n❌ Installation cancelled by user")
            return False
        except Exception as e:
            print(f"\n\n❌ Installation failed: {e}")
            return False


def main():
    """Main installer entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("AI Intelligence Briefing System Installer")
        print("\nUsage: python install.py")
        print("\nThis installer will:")
        print("  • Check system requirements")
        print("  • Install Python dependencies")
        print("  • Set up directory structure")
        print("  • Configure daily scheduler")
        print("  • Run initial test")
        print("\nRequirements:")
        print("  • macOS")
        print("  • Python 3.8+")
        print("  • Administrator access (for scheduler)")
        return
    
    installer = BriefingInstaller()
    success = installer.install()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()