"""
Installation management system for handling package installations
"""
import asyncio
import json
import subprocess
import shlex
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue

from config import BASE_DIR


@dataclass
class InstallationItem:
    """Represents an installable item"""
    id: str
    name: str
    package_manager: str  # brew, npm, pip, cargo, etc.
    install_command: str
    category: str  # cli_tools, mcp_servers, python_packages, etc.
    description: str
    version: Optional[str] = None
    dependencies: List[str] = None
    estimated_size_mb: Optional[int] = None
    documentation_url: Optional[str] = None
    homepage_url: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class InstallationResult:
    """Results of an installation attempt"""
    item_id: str
    success: bool
    duration_seconds: float
    output: str
    error: Optional[str] = None
    installed_version: Optional[str] = None


class PackageDetector:
    """Detects installable packages from intelligence data"""
    
    def __init__(self):
        self.patterns = {
            'homebrew': [
                r'brew install ([a-zA-Z0-9\-_]+)',
                r'(?:using|via|install) Homebrew.*?([a-zA-Z0-9\-_]+)',
                r'(?:^|\s)([a-zA-Z0-9\-_]+)(?:\s+is|\s+can be|\s+available)(?:\s+on|via)?\s+(?:Homebrew|brew)'
            ],
            'npm': [
                r'npm install (?:-g )?([@a-zA-Z0-9\-_/]+)',
                r'npx ([a-zA-Z0-9\-_]+)',
                r'yarn (?:global )?add ([a-zA-Z0-9\-_]+)'
            ],
            'pip': [
                r'pip install ([a-zA-Z0-9\-_]+)',
                r'pip3 install ([a-zA-Z0-9\-_]+)',
                r'python -m pip install ([a-zA-Z0-9\-_]+)'
            ],
            'cargo': [
                r'cargo install ([a-zA-Z0-9\-_]+)'
            ],
            'go': [
                r'go install ([a-zA-Z0-9\-_/.]+)'
            ]
        }
        
        # Known MCP servers and their installation commands
        self.mcp_servers = {
            'filesystem': {
                'install': 'npm install -g @modelcontextprotocol/server-filesystem',
                'description': 'MCP server for filesystem operations'
            },
            'git': {
                'install': 'npm install -g @modelcontextprotocol/server-git', 
                'description': 'MCP server for Git operations'
            },
            'sqlite': {
                'install': 'npm install -g @modelcontextprotocol/server-sqlite',
                'description': 'MCP server for SQLite database operations'
            },
            'postgres': {
                'install': 'npm install -g @modelcontextprotocol/server-postgres',
                'description': 'MCP server for PostgreSQL operations'
            },
            'brave-search': {
                'install': 'npm install -g @modelcontextprotocol/server-brave-search',
                'description': 'MCP server for Brave Search API'
            }
        }
    
    def extract_installable_items(self, intelligence_data: List[Dict[str, Any]]) -> List[InstallationItem]:
        """Extract installable items from intelligence data"""
        items = []
        seen_items = set()
        
        for update in intelligence_data:
            title = update.get('title', '')
            content = update.get('content', '')
            combined_text = f"{title} {content}"
            
            # Extract packages using patterns
            for manager, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, combined_text, re.IGNORECASE)
                    for match in matches:
                        package_name = match.strip()
                        if package_name and package_name not in seen_items:
                            item = self._create_installation_item(
                                package_name, manager, update
                            )
                            if item:
                                items.append(item)
                                seen_items.add(package_name)
        
        # Add known MCP servers
        for name, info in self.mcp_servers.items():
            if name not in seen_items:
                item = InstallationItem(
                    id=f"mcp-{name}",
                    name=name,
                    package_manager='npm',
                    install_command=info['install'],
                    category='mcp_servers',
                    description=info['description'],
                    documentation_url=f"https://modelcontextprotocol.io/servers/{name}"
                )
                items.append(item)
        
        return items
    
    def _create_installation_item(self, package_name: str, manager: str, update: Dict[str, Any]) -> Optional[InstallationItem]:
        """Create an InstallationItem from detected package"""
        try:
            # Generate unique ID
            item_id = hashlib.md5(f"{manager}:{package_name}".encode()).hexdigest()[:12]
            
            # Determine category
            category = self._categorize_package(package_name, manager, update)
            
            # Create install command
            install_command = self._build_install_command(package_name, manager)
            
            # Extract description from update
            description = self._extract_description(package_name, update)
            
            return InstallationItem(
                id=item_id,
                name=package_name,
                package_manager=manager,
                install_command=install_command,
                category=category,
                description=description,
                documentation_url=update.get('url')
            )
            
        except Exception as e:
            print(f"Error creating installation item for {package_name}: {e}")
            return None
    
    def _categorize_package(self, package_name: str, manager: str, update: Dict[str, Any]) -> str:
        """Categorize package based on name and context"""
        title_lower = update.get('title', '').lower()
        content_lower = update.get('content', '').lower()
        combined = f"{title_lower} {content_lower}"
        
        # MCP servers
        if 'mcp' in combined or 'model context protocol' in combined:
            return 'mcp_servers'
        
        # CLI tools
        if any(keyword in combined for keyword in ['cli', 'command line', 'terminal', 'shell']):
            return 'cli_tools'
        
        # Development tools
        if any(keyword in combined for keyword in ['development', 'dev tool', 'developer', 'coding']):
            return 'dev_tools'
        
        # Package manager specific categorization
        category_map = {
            'pip': 'python_packages',
            'npm': 'nodejs_packages',
            'brew': 'homebrew_formulae',
            'cargo': 'rust_crates',
            'go': 'go_modules'
        }
        
        return category_map.get(manager, 'other')
    
    def _build_install_command(self, package_name: str, manager: str) -> str:
        """Build appropriate install command for package and manager"""
        commands = {
            'brew': f"brew install {package_name}",
            'npm': f"npm install -g {package_name}",
            'pip': f"pip install {package_name}",
            'cargo': f"cargo install {package_name}",
            'go': f"go install {package_name}"
        }
        
        return commands.get(manager, f"{manager} install {package_name}")
    
    def _extract_description(self, package_name: str, update: Dict[str, Any]) -> str:
        """Extract description from update content"""
        content = update.get('content', '')
        title = update.get('title', '')
        
        # Try to find a sentence that describes the package
        sentences = content.split('.')
        for sentence in sentences:
            if package_name.lower() in sentence.lower():
                return sentence.strip()[:200]
        
        # Fallback to title or generic description
        if title:
            return title[:100]
        
        return f"Package: {package_name}"


class InstallationQueue:
    """Manages installation queue with progress tracking"""
    
    def __init__(self):
        self.queue = Queue()
        self.active_installations = {}
        self.completed_installations = {}
        self.failed_installations = {}
        self.progress_callbacks = []
        self.lock = threading.Lock()
    
    def add_items(self, items: List[InstallationItem]) -> str:
        """Add items to installation queue, returns batch ID"""
        batch_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
        
        for item in items:
            self.queue.put((batch_id, item))
        
        return batch_id
    
    def get_progress(self, batch_id: str = None) -> Dict[str, Any]:
        """Get installation progress"""
        with self.lock:
            if batch_id:
                # Return progress for specific batch
                active = {k: v for k, v in self.active_installations.items() 
                         if v.get('batch_id') == batch_id}
                completed = {k: v for k, v in self.completed_installations.items() 
                           if v.get('batch_id') == batch_id}
                failed = {k: v for k, v in self.failed_installations.items() 
                        if v.get('batch_id') == batch_id}
            else:
                # Return all progress
                active = self.active_installations.copy()
                completed = self.completed_installations.copy()
                failed = self.failed_installations.copy()
            
            return {
                'active': active,
                'completed': completed,
                'failed': failed,
                'queue_size': self.queue.qsize(),
                'total_active': len(active),
                'total_completed': len(completed),
                'total_failed': len(failed)
            }
    
    def register_progress_callback(self, callback):
        """Register callback for progress updates"""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, event_type: str, item_id: str, data: Dict[str, Any]):
        """Notify registered callbacks of progress"""
        for callback in self.progress_callbacks:
            try:
                callback(event_type, item_id, data)
            except Exception as e:
                print(f"Progress callback error: {e}")


class SecurityValidator:
    """Validates installation commands for security"""
    
    def __init__(self):
        # Dangerous patterns that should be blocked
        self.dangerous_patterns = [
            r'sudo\s+rm\s+-rf\s*/',
            r'curl.*?\|\s*(?:bash|sh|zsh)',
            r'wget.*?\|\s*(?:bash|sh|zsh)',
            r'dd\s+if=.*of=.*',
            r'mkfs\.',
            r'format\s+[cC]:',
            r'del\s+/[qfs]\s+[cC]:',
            r'rm\s+-rf\s+\$HOME',
            r'chmod\s+777\s+/',
        ]
        
        # Allowed package managers and their safe commands
        self.safe_managers = {
            'brew': ['install', 'upgrade', 'info', 'search'],
            'npm': ['install', 'update', 'info', 'search'],
            'pip': ['install', 'upgrade', 'show', 'search'],
            'cargo': ['install', 'update', 'search'],
            'go': ['install', 'get', 'mod']
        }
    
    def validate_command(self, command: str) -> tuple[bool, Optional[str]]:
        """Validate if command is safe to execute"""
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Command contains dangerous pattern: {pattern}"
        
        # Check if using approved package managers
        command_parts = shlex.split(command)
        if not command_parts:
            return False, "Empty command"
        
        manager = command_parts[0]
        if manager not in self.safe_managers:
            return False, f"Package manager '{manager}' not in approved list"
        
        if len(command_parts) > 1:
            action = command_parts[1]
            if action not in self.safe_managers[manager]:
                return False, f"Action '{action}' not allowed for {manager}"
        
        return True, None
    
    def sanitize_package_name(self, package_name: str) -> str:
        """Sanitize package name"""
        # Remove dangerous characters and limit length
        sanitized = re.sub(r'[^a-zA-Z0-9\-_@/.]', '', package_name)
        return sanitized[:100]  # Limit length


class InstallationManager:
    """Main installation management system"""
    
    def __init__(self):
        self.detector = PackageDetector()
        self.queue = InstallationQueue()
        self.validator = SecurityValidator()
        self.executor = ThreadPoolExecutor(max_workers=3)  # Limit concurrent installations
        self.logger = self._setup_logger()
        self.installation_log_path = BASE_DIR / 'logs' / 'installations.log'
        self.installation_log_path.parent.mkdir(exist_ok=True)
        
        # Start background worker
        self._start_worker()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for installation manager"""
        logger = logging.getLogger('installation_manager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler(BASE_DIR / 'logs' / 'installation_manager.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def detect_installable_items(self, intelligence_data: List[Dict[str, Any]]) -> List[InstallationItem]:
        """Detect installable items from intelligence data"""
        return self.detector.extract_installable_items(intelligence_data)
    
    def queue_installations(self, items: List[InstallationItem]) -> tuple[str, List[str]]:
        """Queue items for installation, returns batch_id and list of rejected items"""
        validated_items = []
        rejected_items = []
        
        for item in items:
            # Validate installation command
            is_valid, error_msg = self.validator.validate_command(item.install_command)
            if is_valid:
                # Sanitize package name
                item.name = self.validator.sanitize_package_name(item.name)
                validated_items.append(item)
            else:
                rejected_items.append(f"{item.name}: {error_msg}")
                self.logger.warning(f"Rejected installation of {item.name}: {error_msg}")
        
        if validated_items:
            batch_id = self.queue.add_items(validated_items)
            self.logger.info(f"Queued {len(validated_items)} items for installation (batch: {batch_id})")
            return batch_id, rejected_items
        else:
            return None, rejected_items
    
    def get_installation_progress(self, batch_id: str = None) -> Dict[str, Any]:
        """Get installation progress"""
        return self.queue.get_progress(batch_id)
    
    def _start_worker(self):
        """Start background worker for processing installations"""
        def worker():
            while True:
                try:
                    batch_id, item = self.queue.queue.get(timeout=1)
                    self._process_installation(batch_id, item)
                    self.queue.queue.task_done()
                except Exception as e:
                    if "Empty queue" not in str(e):
                        self.logger.error(f"Worker error: {e}")
                        
        # Start worker thread
        worker_thread = threading.Thread(target=worker, daemon=True)
        worker_thread.start()
    
    def _process_installation(self, batch_id: str, item: InstallationItem):
        """Process a single installation"""
        start_time = datetime.now()
        
        # Mark as active
        with self.queue.lock:
            self.queue.active_installations[item.id] = {
                'batch_id': batch_id,
                'item': asdict(item),
                'start_time': start_time.isoformat(),
                'status': 'installing'
            }
        
        try:
            self.logger.info(f"Starting installation of {item.name} (ID: {item.id})")
            
            # Execute installation command
            result = self._execute_installation_command(item)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Move to appropriate completion dict
            with self.queue.lock:
                del self.queue.active_installations[item.id]
                
                completion_data = {
                    'batch_id': batch_id,
                    'item': asdict(item),
                    'result': asdict(result),
                    'completed_at': datetime.now().isoformat(),
                    'duration_seconds': duration
                }
                
                if result.success:
                    self.queue.completed_installations[item.id] = completion_data
                    self.logger.info(f"Successfully installed {item.name} in {duration:.1f}s")
                else:
                    self.queue.failed_installations[item.id] = completion_data
                    self.logger.error(f"Failed to install {item.name}: {result.error}")
            
            # Log to installation log file
            self._log_installation_result(batch_id, item, result, duration)
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            # Move to failed
            with self.queue.lock:
                if item.id in self.queue.active_installations:
                    del self.queue.active_installations[item.id]
                
                self.queue.failed_installations[item.id] = {
                    'batch_id': batch_id,
                    'item': asdict(item),
                    'error': error_msg,
                    'completed_at': datetime.now().isoformat(),
                    'duration_seconds': duration
                }
            
            self.logger.error(f"Exception during installation of {item.name}: {e}")
    
    def _execute_installation_command(self, item: InstallationItem) -> InstallationResult:
        """Execute the actual installation command"""
        start_time = datetime.now()
        
        try:
            # Run command with timeout
            result = subprocess.run(
                shlex.split(item.install_command),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=False
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Determine success
            success = result.returncode == 0
            
            # Extract installed version if possible
            installed_version = self._extract_version_from_output(
                result.stdout, item.package_manager, item.name
            )
            
            return InstallationResult(
                item_id=item.id,
                success=success,
                duration_seconds=duration,
                output=result.stdout,
                error=result.stderr if not success else None,
                installed_version=installed_version
            )
            
        except subprocess.TimeoutExpired:
            return InstallationResult(
                item_id=item.id,
                success=False,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                output="",
                error="Installation timed out after 5 minutes"
            )
        except Exception as e:
            return InstallationResult(
                item_id=item.id,
                success=False,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                output="",
                error=str(e)
            )
    
    def _extract_version_from_output(self, output: str, manager: str, package_name: str) -> Optional[str]:
        """Extract installed version from command output"""
        try:
            # Try to run version command for the installed package
            version_commands = {
                'npm': f"{package_name} --version",
                'pip': f"{package_name} --version",
                'cargo': f"{package_name} --version",
                'brew': f"brew list --versions {package_name}"
            }
            
            if manager in version_commands:
                try:
                    version_result = subprocess.run(
                        shlex.split(version_commands[manager]),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if version_result.returncode == 0:
                        # Extract version number from output
                        version_match = re.search(r'(\d+\.\d+\.\d+)', version_result.stdout)
                        if version_match:
                            return version_match.group(1)
                except:
                    pass
            
            # Fallback: look for version in installation output
            version_patterns = [
                rf'{re.escape(package_name)}@(\d+\.\d+\.\d+)',
                r'version[:\s]+(\d+\.\d+\.\d+)',
                r'v(\d+\.\d+\.\d+)',
                r'(\d+\.\d+\.\d+)'
            ]
            
            for pattern in version_patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    return match.group(1)
            
        except Exception:
            pass
        
        return None
    
    def _log_installation_result(self, batch_id: str, item: InstallationItem, 
                                result: InstallationResult, duration: float):
        """Log installation result to file"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'batch_id': batch_id,
            'item_id': item.id,
            'package_name': item.name,
            'package_manager': item.package_manager,
            'command': item.install_command,
            'success': result.success,
            'duration_seconds': duration,
            'installed_version': result.installed_version,
            'error': result.error
        }
        
        with open(self.installation_log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_installation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get installation history from log file"""
        history = []
        
        try:
            if self.installation_log_path.exists():
                with open(self.installation_log_path, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            history.append(entry)
                        except:
                            continue
                
                # Return most recent entries first
                history.reverse()
                return history[:limit]
        except Exception as e:
            self.logger.error(f"Error reading installation history: {e}")
        
        return history
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old installation logs"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            if self.installation_log_path.exists():
                lines_to_keep = []
                
                with open(self.installation_log_path, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_date = datetime.fromisoformat(entry['timestamp'])
                            if entry_date >= cutoff_date:
                                lines_to_keep.append(line)
                        except:
                            # Keep malformed lines just in case
                            lines_to_keep.append(line)
                
                # Rewrite file with only recent entries
                with open(self.installation_log_path, 'w') as f:
                    f.writelines(lines_to_keep)
                
                removed_count = len(lines_to_keep)
                self.logger.info(f"Cleaned up installation log, removed {removed_count} old entries")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up installation logs: {e}")


def main():
    """Test the installation manager"""
    manager = InstallationManager()
    
    # Test data
    test_data = [
        {
            'title': 'New CLI tool: jq for JSON processing',
            'content': 'Install jq using brew install jq for command-line JSON processing',
            'url': 'https://github.com/stedolan/jq'
        }
    ]
    
    # Detect installable items
    items = manager.detect_installable_items(test_data)
    print(f"Detected {len(items)} installable items:")
    for item in items:
        print(f"  - {item.name} ({item.package_manager}): {item.description}")


if __name__ == "__main__":
    main()