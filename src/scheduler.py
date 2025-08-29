"""
Scheduler for daily intelligence briefing system (macOS launchd)
"""
import os
import sys
import subprocess
import webbrowser
from datetime import datetime, time
from pathlib import Path
from typing import Dict, Any
import plistlib

from config import BASE_DIR, REPORTS_DIR, REPORT_GENERATION_TIME, REPORT_READY_TIME


class SchedulerManager:
    """Manages macOS launchd scheduling for the briefing system"""
    
    def __init__(self):
        self.home_dir = Path.home()
        self.launchd_dir = self.home_dir / "Library" / "LaunchAgents"
        self.launchd_dir.mkdir(parents=True, exist_ok=True)
        
        self.plist_name = "com.ai.intelligence.briefing"
        self.plist_path = self.launchd_dir / f"{self.plist_name}.plist"
        
        # Path to the main script
        self.main_script = BASE_DIR / "run_briefing.py"
        self.python_executable = self._find_python_executable()
    
    def _find_python_executable(self) -> str:
        """Find the appropriate Python executable"""
        # Check if we're in a virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            return sys.executable
        
        # Try common Python locations
        python_paths = [
            "/usr/local/bin/python3",
            "/opt/homebrew/bin/python3",
            "/usr/bin/python3",
            "python3",
            "python"
        ]
        
        for python_path in python_paths:
            try:
                result = subprocess.run([python_path, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and "Python 3" in result.stdout:
                    return python_path
            except:
                continue
        
        # Fallback to sys.executable
        return sys.executable
    
    def create_launchd_plist(self) -> None:
        """Create launchd plist for scheduling"""
        # Parse time string
        hour, minute = map(int, REPORT_GENERATION_TIME.split(':'))
        
        plist_content = {
            'Label': self.plist_name,
            'ProgramArguments': [
                self.python_executable,
                str(self.main_script)
            ],
            'StartCalendarInterval': {
                'Hour': hour,
                'Minute': minute
            },
            'StandardOutPath': str(BASE_DIR / 'logs' / 'briefing.log'),
            'StandardErrorPath': str(BASE_DIR / 'logs' / 'briefing_error.log'),
            'WorkingDirectory': str(BASE_DIR),
            'RunAtLoad': False,
            'KeepAlive': False,
            'LaunchOnlyOnce': False
        }
        
        # Ensure log directory exists
        log_dir = BASE_DIR / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Write plist file
        with open(self.plist_path, 'wb') as f:
            plistlib.dump(plist_content, f)
        
        print(f"Created launchd plist at: {self.plist_path}")
    
    def install_scheduler(self) -> bool:
        """Install the launchd job"""
        try:
            # Create the plist file
            self.create_launchd_plist()
            
            # Load the job
            result = subprocess.run([
                'launchctl', 'load', str(self.plist_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Successfully installed scheduler: {self.plist_name}")
                print(f"Reports will be generated daily at {REPORT_GENERATION_TIME}")
                return True
            else:
                print(f"Error installing scheduler: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error installing scheduler: {e}")
            return False
    
    def uninstall_scheduler(self) -> bool:
        """Uninstall the launchd job"""
        try:
            # Unload the job
            result = subprocess.run([
                'launchctl', 'unload', str(self.plist_path)
            ], capture_output=True, text=True)
            
            # Remove the plist file
            if self.plist_path.exists():
                self.plist_path.unlink()
                print(f"Removed plist file: {self.plist_path}")
            
            print(f"Successfully uninstalled scheduler: {self.plist_name}")
            return True
            
        except Exception as e:
            print(f"Error uninstalling scheduler: {e}")
            return False
    
    def check_scheduler_status(self) -> Dict[str, Any]:
        """Check the status of the scheduled job"""
        try:
            result = subprocess.run([
                'launchctl', 'list', self.plist_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and len(lines) > 0 and lines[0] != '':
                    # Job is loaded
                    if len(lines) >= 1:
                        parts = lines[0].split('\t')
                        if len(parts) >= 3:
                            return {
                                'installed': True,
                                'pid': parts[0] if parts[0] != '-' else None,
                                'last_exit_code': parts[1] if parts[1] != '-' else None,
                                'label': parts[2]
                            }
                        else:
                            return {
                                'installed': True,
                                'status': 'loaded but details unavailable'
                            }
            
            # Check if plist file exists
            if self.plist_path.exists():
                return {
                    'installed': True,
                    'status': 'plist exists but not loaded'
                }
            else:
                return {'installed': False}
            
        except Exception as e:
            return {'installed': False, 'error': str(e)}
    
    def trigger_now(self) -> bool:
        """Manually trigger the briefing generation"""
        try:
            result = subprocess.run([
                self.python_executable,
                str(self.main_script),
                '--force'
            ], cwd=str(BASE_DIR), capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Briefing generated successfully")
                print(result.stdout)
                return True
            else:
                print(f"Error generating briefing: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error triggering briefing: {e}")
            return False


class BrowserManager:
    """Manages automatic browser opening"""
    
    @staticmethod
    def open_latest_report() -> bool:
        """Open the latest report in the default browser"""
        try:
            # Find the latest report file
            report_files = list(REPORTS_DIR.glob("ai_briefing_*.html"))
            
            if not report_files:
                print("No report files found")
                return False
            
            # Get the latest report
            latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
            
            # Open in browser
            webbrowser.open(f"file://{latest_report.absolute()}")
            print(f"Opened report in browser: {latest_report}")
            return True
            
        except Exception as e:
            print(f"Error opening report in browser: {e}")
            return False
    
    @staticmethod
    def should_auto_open() -> bool:
        """Check if we should auto-open the browser based on time"""
        current_time = datetime.now().time()
        ready_time = time(*map(int, REPORT_READY_TIME.split(':')))
        
        # Auto-open if it's within 10 minutes of the ready time
        time_diff = datetime.combine(datetime.today(), current_time) - datetime.combine(datetime.today(), ready_time)
        
        return abs(time_diff.total_seconds()) <= 600  # 10 minutes


# Notification system for macOS
class NotificationManager:
    """Manages system notifications"""
    
    @staticmethod
    def send_notification(title: str, message: str, subtitle: str = None) -> None:
        """Send a macOS notification"""
        try:
            cmd = [
                'osascript', '-e',
                f'display notification "{message}" with title "{title}"'
            ]
            
            if subtitle:
                cmd[-1] += f' subtitle "{subtitle}"'
            
            subprocess.run(cmd, capture_output=True)
            
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    @staticmethod
    def notify_report_ready(report_path: str) -> None:
        """Send notification when report is ready"""
        NotificationManager.send_notification(
            "AI Intelligence Briefing",
            "Your daily briefing is ready!",
            f"Report generated at {datetime.now().strftime('%I:%M %p')}"
        )
    
    @staticmethod
    def notify_error(error_message: str) -> None:
        """Send notification when an error occurs"""
        NotificationManager.send_notification(
            "AI Intelligence Briefing - Error",
            error_message,
            "Check logs for details"
        )


# Main scheduling functions
def setup_scheduler():
    """Set up the daily scheduler"""
    scheduler = SchedulerManager()
    return scheduler.install_scheduler()


def remove_scheduler():
    """Remove the daily scheduler"""
    scheduler = SchedulerManager()
    return scheduler.uninstall_scheduler()


def check_scheduler():
    """Check scheduler status"""
    scheduler = SchedulerManager()
    status = scheduler.check_scheduler_status()
    
    print("Scheduler Status:")
    if status['installed']:
        print(f"  Status: Installed and active")
        print(f"  Label: {status.get('label', 'N/A')}")
        if status.get('pid'):
            print(f"  Running PID: {status['pid']}")
        if status.get('last_exit_code'):
            print(f"  Last exit code: {status['last_exit_code']}")
    else:
        print(f"  Status: Not installed")
        if 'error' in status:
            print(f"  Error: {status['error']}")
    
    return status


def run_now():
    """Run the briefing generation immediately"""
    scheduler = SchedulerManager()
    return scheduler.trigger_now()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "install":
            setup_scheduler()
        elif command == "uninstall":
            remove_scheduler()
        elif command == "status":
            check_scheduler()
        elif command == "run":
            run_now()
        else:
            print("Usage: python scheduler.py [install|uninstall|status|run]")
    else:
        print("Usage: python scheduler.py [install|uninstall|status|run]")