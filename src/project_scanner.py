"""
Project scanner for analyzing local Claude Code projects
"""
import os
import json
import subprocess
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import re
import ast
import hashlib

from config import BASE_DIR


class ProjectScanner:
    """Scans and analyzes local Claude Code projects"""
    
    def __init__(self):
        self.base_paths = [
            Path.home(),
            Path('/Users'),
            Path('/home'),
            Path('/mnt'),
            Path('/opt'),
            Path('/usr/local')
        ]
        self.ignore_patterns = {
            'node_modules', '.git', 'venv', '__pycache__', '.vscode', 
            '.idea', 'dist', 'build', 'target', '.next', '.nuxt',
            'coverage', '.pytest_cache', '.mypy_cache'
        }
        self.project_indicators = {
            'package.json': 'nodejs',
            'requirements.txt': 'python', 
            'Pipfile': 'python',
            'pyproject.toml': 'python',
            'Cargo.toml': 'rust',
            'go.mod': 'go',
            'pom.xml': 'java',
            'build.gradle': 'java',
            'composer.json': 'php',
            'Gemfile': 'ruby',
            'mix.exs': 'elixir',
            'Package.swift': 'swift',
            'pubspec.yaml': 'dart'
        }
    
    def scan_projects(self, max_depth: int = 4) -> List[Dict[str, Any]]:
        """Scan for projects and analyze them"""
        projects = []
        
        for base_path in self.base_paths:
            if not base_path.exists():
                continue
                
            try:
                found_projects = self._find_projects(base_path, max_depth)
                for project_path in found_projects:
                    try:
                        project_info = self._analyze_project(project_path)
                        if project_info:
                            projects.append(project_info)
                    except Exception as e:
                        print(f"Error analyzing project {project_path}: {e}")
                        continue
            except PermissionError:
                continue
        
        return projects
    
    def _find_projects(self, base_path: Path, max_depth: int) -> List[Path]:
        """Find potential project directories"""
        projects = []
        
        def _scan_recursive(current_path: Path, depth: int):
            if depth >= max_depth:
                return
                
            try:
                for item in current_path.iterdir():
                    if not item.is_dir():
                        continue
                    
                    item_name = item.name
                    if item_name.startswith('.') and item_name not in {'.github', '.gitlab'}:
                        continue
                    
                    if item_name in self.ignore_patterns:
                        continue
                    
                    # Check if this directory contains project indicators
                    for indicator, project_type in self.project_indicators.items():
                        if (item / indicator).exists():
                            projects.append(item)
                            break
                    else:
                        # Recurse into subdirectories
                        _scan_recursive(item, depth + 1)
            except (PermissionError, OSError):
                pass
        
        _scan_recursive(base_path, 0)
        return projects
    
    def _analyze_project(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a single project"""
        try:
            # Basic project info
            project_info = {
                'path': str(project_path),
                'name': project_path.name,
                'type': self._detect_project_type(project_path),
                'last_modified': datetime.fromtimestamp(project_path.stat().st_mtime),
                'size_mb': self._get_directory_size(project_path),
                'git_info': self._get_git_info(project_path),
                'dependencies': self._analyze_dependencies(project_path),
                'code_quality': self._analyze_code_quality(project_path),
                'todos': self._extract_todos(project_path),
                'health_score': 0,
                'recommendations': [],
                'security_issues': []
            }
            
            # Calculate health score and generate recommendations
            self._calculate_health_score(project_info)
            self._generate_recommendations(project_info)
            
            return project_info
            
        except Exception as e:
            print(f"Error analyzing {project_path}: {e}")
            return None
    
    def _detect_project_type(self, project_path: Path) -> str:
        """Detect the primary project type"""
        for indicator, project_type in self.project_indicators.items():
            if (project_path / indicator).exists():
                return project_type
        
        # Check for common file extensions if no clear indicator
        extensions = {}
        try:
            for file_path in project_path.rglob('*'):
                if file_path.is_file() and file_path.suffix:
                    ext = file_path.suffix.lower()
                    extensions[ext] = extensions.get(ext, 0) + 1
        except:
            pass
        
        if extensions:
            most_common = max(extensions.items(), key=lambda x: x[1])[0]
            type_mapping = {
                '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                '.java': 'java', '.rs': 'rust', '.go': 'go',
                '.php': 'php', '.rb': 'ruby', '.swift': 'swift'
            }
            return type_mapping.get(most_common, 'unknown')
        
        return 'unknown'
    
    def _get_directory_size(self, path: Path) -> float:
        """Get directory size in MB"""
        try:
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except:
                        continue
            return round(total_size / (1024 * 1024), 2)
        except:
            return 0
    
    def _get_git_info(self, project_path: Path) -> Dict[str, Any]:
        """Get Git repository information"""
        git_info = {
            'is_repo': False,
            'branch': None,
            'uncommitted_changes': False,
            'last_commit': None,
            'remote_url': None,
            'ahead_behind': {'ahead': 0, 'behind': 0}
        }
        
        git_dir = project_path / '.git'
        if not git_dir.exists():
            return git_info
        
        git_info['is_repo'] = True
        
        try:
            # Get current branch
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=project_path, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                git_info['branch'] = result.stdout.strip()
            
            # Check for uncommitted changes
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=project_path, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                git_info['uncommitted_changes'] = bool(result.stdout.strip())
            
            # Get last commit info
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%H|%s|%cd'],
                cwd=project_path, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split('|')
                if len(parts) >= 3:
                    git_info['last_commit'] = {
                        'hash': parts[0],
                        'message': parts[1],
                        'date': parts[2]
                    }
            
            # Get remote URL
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=project_path, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                git_info['remote_url'] = result.stdout.strip()
            
            # Check ahead/behind status
            if git_info['branch'] and git_info['remote_url']:
                result = subprocess.run(
                    ['git', 'rev-list', '--left-right', '--count', f"origin/{git_info['branch']}...HEAD"],
                    cwd=project_path, capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split('\t')
                    if len(parts) == 2:
                        git_info['ahead_behind'] = {
                            'behind': int(parts[0]),
                            'ahead': int(parts[1])
                        }
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
            pass
        
        return git_info
    
    def _analyze_dependencies(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project dependencies"""
        dependencies = {
            'total_count': 0,
            'outdated_count': 0,
            'vulnerable_count': 0,
            'dependencies': [],
            'package_files': []
        }
        
        # Python dependencies
        for req_file in ['requirements.txt', 'Pipfile', 'pyproject.toml']:
            req_path = project_path / req_file
            if req_path.exists():
                dependencies['package_files'].append(req_file)
                deps = self._parse_python_dependencies(req_path)
                dependencies['dependencies'].extend(deps)
        
        # Node.js dependencies
        package_json_path = project_path / 'package.json'
        if package_json_path.exists():
            dependencies['package_files'].append('package.json')
            deps = self._parse_nodejs_dependencies(package_json_path)
            dependencies['dependencies'].extend(deps)
        
        # Rust dependencies
        cargo_path = project_path / 'Cargo.toml'
        if cargo_path.exists():
            dependencies['package_files'].append('Cargo.toml')
            deps = self._parse_cargo_dependencies(cargo_path)
            dependencies['dependencies'].extend(deps)
        
        dependencies['total_count'] = len(dependencies['dependencies'])
        
        return dependencies
    
    def _parse_python_dependencies(self, req_path: Path) -> List[Dict[str, Any]]:
        """Parse Python dependencies from requirements files"""
        deps = []
        try:
            with open(req_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Simple parsing - can be enhanced
                    match = re.match(r'^([a-zA-Z0-9\-_]+)([><=!~]*)([\d\.]+.*)?', line)
                    if match:
                        deps.append({
                            'name': match.group(1),
                            'version': match.group(3) or 'latest',
                            'type': 'python',
                            'file': req_path.name
                        })
        except Exception:
            pass
        
        return deps
    
    def _parse_nodejs_dependencies(self, package_json_path: Path) -> List[Dict[str, Any]]:
        """Parse Node.js dependencies from package.json"""
        deps = []
        try:
            with open(package_json_path, 'r') as f:
                data = json.load(f)
            
            for dep_type in ['dependencies', 'devDependencies']:
                if dep_type in data:
                    for name, version in data[dep_type].items():
                        deps.append({
                            'name': name,
                            'version': version,
                            'type': 'nodejs',
                            'file': 'package.json',
                            'dev_dependency': dep_type == 'devDependencies'
                        })
        except Exception:
            pass
        
        return deps
    
    def _parse_cargo_dependencies(self, cargo_path: Path) -> List[Dict[str, Any]]:
        """Parse Rust dependencies from Cargo.toml"""
        deps = []
        try:
            with open(cargo_path, 'r') as f:
                content = f.read()
            
            # Simple TOML parsing for dependencies section
            in_deps = False
            for line in content.split('\n'):
                line = line.strip()
                if line == '[dependencies]':
                    in_deps = True
                    continue
                elif line.startswith('[') and line.endswith(']'):
                    in_deps = False
                    continue
                
                if in_deps and '=' in line:
                    parts = line.split('=', 1)
                    name = parts[0].strip()
                    version = parts[1].strip().strip('"\'')
                    deps.append({
                        'name': name,
                        'version': version,
                        'type': 'rust',
                        'file': 'Cargo.toml'
                    })
        except Exception:
            pass
        
        return deps
    
    def _analyze_code_quality(self, project_path: Path) -> Dict[str, Any]:
        """Analyze code quality metrics"""
        quality = {
            'linting_issues': 0,
            'test_coverage': 0,
            'test_files_count': 0,
            'documentation_score': 0,
            'complexity_score': 0,
            'issues': []
        }
        
        # Count test files
        test_patterns = ['*test*.py', '*_test.py', 'test_*.py', '*.test.js', '*.spec.js']
        for pattern in test_patterns:
            quality['test_files_count'] += len(list(project_path.rglob(pattern)))
        
        # Check for documentation
        doc_files = ['README.md', 'README.rst', 'docs/', 'doc/']
        doc_count = 0
        for doc_item in doc_files:
            if (project_path / doc_item).exists():
                doc_count += 1
        quality['documentation_score'] = min(doc_count * 25, 100)
        
        # Simple complexity analysis
        quality['complexity_score'] = self._estimate_complexity(project_path)
        
        return quality
    
    def _estimate_complexity(self, project_path: Path) -> int:
        """Estimate project complexity (0-100)"""
        try:
            total_lines = 0
            total_functions = 0
            total_classes = 0
            
            for py_file in project_path.rglob('*.py'):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        total_lines += len(content.splitlines())
                        
                        # Parse AST for functions and classes
                        try:
                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    total_functions += 1
                                elif isinstance(node, ast.ClassDef):
                                    total_classes += 1
                        except:
                            pass
                except:
                    continue
            
            # Simple scoring based on size and structure
            if total_lines == 0:
                return 0
            
            complexity = min(
                (total_lines // 100) + 
                (total_functions // 10) + 
                (total_classes // 5),
                100
            )
            
            return complexity
        except:
            return 50  # Default medium complexity
    
    def _extract_todos(self, project_path: Path) -> List[Dict[str, Any]]:
        """Extract TODO/FIXME comments from code"""
        todos = []
        todo_patterns = [
            r'(?i)#\s*(TODO|FIXME|HACK|BUG):?\s*(.+)',
            r'(?i)//\s*(TODO|FIXME|HACK|BUG):?\s*(.+)',
            r'(?i)/\*\s*(TODO|FIXME|HACK|BUG):?\s*(.+)\s*\*/',
        ]
        
        file_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.rs', '.go']
        
        for ext in file_extensions:
            for file_path in project_path.rglob(f'*{ext}'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                        for line_num, line in enumerate(lines, 1):
                            for pattern in todo_patterns:
                                match = re.search(pattern, line)
                                if match:
                                    todos.append({
                                        'type': match.group(1).upper(),
                                        'text': match.group(2).strip(),
                                        'file': str(file_path.relative_to(project_path)),
                                        'line': line_num
                                    })
                except:
                    continue
        
        return todos
    
    def _calculate_health_score(self, project_info: Dict[str, Any]) -> None:
        """Calculate overall project health score (0-100)"""
        score = 100
        
        # Git health
        git_info = project_info['git_info']
        if not git_info['is_repo']:
            score -= 15
        elif git_info['uncommitted_changes']:
            score -= 5
        
        if git_info['ahead_behind']['behind'] > 5:
            score -= 10
        
        # Dependencies health
        deps = project_info['dependencies']
        if deps['total_count'] > 50:
            score -= 10
        if deps['outdated_count'] > deps['total_count'] * 0.3:
            score -= 15
        
        # Code quality
        quality = project_info['code_quality']
        if quality['test_files_count'] == 0:
            score -= 20
        if quality['documentation_score'] < 50:
            score -= 10
        
        # TODOs
        todo_count = len(project_info['todos'])
        if todo_count > 10:
            score -= 10
        elif todo_count > 20:
            score -= 20
        
        # Size considerations
        if project_info['size_mb'] > 1000:  # Very large projects
            score -= 5
        
        project_info['health_score'] = max(0, min(100, score))
    
    def _generate_recommendations(self, project_info: Dict[str, Any]) -> None:
        """Generate AI-powered recommendations"""
        recommendations = []
        
        # Git recommendations
        git_info = project_info['git_info']
        if not git_info['is_repo']:
            recommendations.append({
                'priority': 'high',
                'category': 'version_control',
                'title': 'Initialize Git Repository',
                'description': 'This project is not under version control. Initialize git to track changes.',
                'action': 'git init',
                'estimated_time': '2 minutes'
            })
        elif git_info['uncommitted_changes']:
            recommendations.append({
                'priority': 'medium',
                'category': 'version_control',
                'title': 'Commit Pending Changes',
                'description': 'You have uncommitted changes. Commit them to preserve your work.',
                'action': 'git add -A && git commit -m "Save current changes"',
                'estimated_time': '5 minutes'
            })
        
        if git_info['ahead_behind']['behind'] > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'version_control',
                'title': f'Pull Latest Changes',
                'description': f'Your branch is {git_info["ahead_behind"]["behind"]} commits behind remote.',
                'action': 'git pull',
                'estimated_time': '2 minutes'
            })
        
        # Dependencies recommendations
        deps = project_info['dependencies']
        if deps['total_count'] == 0 and project_info['type'] != 'unknown':
            recommendations.append({
                'priority': 'low',
                'category': 'dependencies',
                'title': 'Add Dependency Management',
                'description': 'Consider adding a dependency file for better project management.',
                'action': f'Create {self._get_dep_file_for_type(project_info["type"])}',
                'estimated_time': '10 minutes'
            })
        
        # Documentation recommendations
        quality = project_info['code_quality']
        if quality['documentation_score'] < 50:
            recommendations.append({
                'priority': 'low',
                'category': 'documentation',
                'title': 'Improve Documentation',
                'description': 'Add a README file and document your code better.',
                'action': 'Create README.md with project description and usage',
                'estimated_time': '30 minutes'
            })
        
        # Testing recommendations
        if quality['test_files_count'] == 0:
            recommendations.append({
                'priority': 'high',
                'category': 'testing',
                'title': 'Add Unit Tests',
                'description': 'No test files found. Add unit tests to ensure code reliability.',
                'action': f'Create test files using {self._get_test_framework(project_info["type"])}',
                'estimated_time': '2 hours'
            })
        
        # TODO cleanup
        todo_count = len(project_info['todos'])
        if todo_count > 5:
            recommendations.append({
                'priority': 'medium',
                'category': 'maintenance',
                'title': f'Address {todo_count} TODO Items',
                'description': 'Clean up TODO and FIXME comments in your codebase.',
                'action': 'Review and resolve outstanding TODO items',
                'estimated_time': f'{todo_count * 10} minutes'
            })
        
        # Security recommendations
        if project_info['type'] == 'python':
            req_files = [f for f in deps['package_files'] if 'requirements' in f]
            if req_files:
                recommendations.append({
                    'priority': 'high',
                    'category': 'security',
                    'title': 'Security Audit',
                    'description': 'Run security audit on Python dependencies.',
                    'action': 'pip install safety && safety check',
                    'estimated_time': '5 minutes'
                })
        
        project_info['recommendations'] = recommendations
    
    def _get_dep_file_for_type(self, project_type: str) -> str:
        """Get appropriate dependency file for project type"""
        mapping = {
            'python': 'requirements.txt',
            'nodejs': 'package.json',
            'rust': 'Cargo.toml',
            'go': 'go.mod',
            'java': 'pom.xml',
            'php': 'composer.json',
            'ruby': 'Gemfile'
        }
        return mapping.get(project_type, 'requirements file')
    
    def _get_test_framework(self, project_type: str) -> str:
        """Get appropriate test framework for project type"""
        mapping = {
            'python': 'pytest or unittest',
            'nodejs': 'Jest or Mocha',
            'rust': 'built-in cargo test',
            'go': 'built-in go test',
            'java': 'JUnit',
            'php': 'PHPUnit',
            'ruby': 'RSpec'
        }
        return mapping.get(project_type, 'appropriate test framework')


def main():
    """Test the project scanner"""
    scanner = ProjectScanner()
    projects = scanner.scan_projects(max_depth=3)
    
    print(f"Found {len(projects)} projects:")
    for project in projects[:5]:  # Show first 5 projects
        print(f"\nProject: {project['name']}")
        print(f"  Type: {project['type']}")
        print(f"  Health Score: {project['health_score']}/100")
        print(f"  Recommendations: {len(project['recommendations'])}")
        print(f"  Git Repo: {project['git_info']['is_repo']}")
        print(f"  Dependencies: {project['dependencies']['total_count']}")


if __name__ == "__main__":
    main()