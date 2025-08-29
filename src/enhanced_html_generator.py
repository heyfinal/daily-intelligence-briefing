"""
Enhanced HTML report generator with project status and installation features
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Template, Environment, FileSystemLoader

from config import REPORTS_DIR, REPORT_CONFIG, CONTENT_CATEGORIES, BASE_DIR
from database import DatabaseManager
from project_scanner import ProjectScanner
from installation_manager import InstallationManager


class EnhancedHTMLGenerator:
    """Enhanced HTML generator with all new features"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.project_scanner = ProjectScanner()
        self.installation_manager = InstallationManager()
        self.template_dir = BASE_DIR / "templates"
        self.template_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Add custom filters
        self.env.filters['from_json'] = self._from_json_filter
        
        # Ensure enhanced templates exist
        self._ensure_enhanced_templates()
    
    def _ensure_enhanced_templates(self):
        """Ensure enhanced templates exist"""
        enhanced_template_path = self.template_dir / "enhanced_main.html"
        enhanced_css_path = self.template_dir / "enhanced_styles.css"
        enhanced_js_path = self.template_dir / "enhanced_script.js"
        
        # Check if enhanced files exist - if not, copy from created files
        for file_path in [enhanced_template_path, enhanced_css_path, enhanced_js_path]:
            if not file_path.exists():
                print(f"Warning: Enhanced template {file_path.name} not found.")
    
    def generate_enhanced_report(self, report_date: datetime = None) -> str:
        """Generate enhanced HTML report with all new features"""
        if report_date is None:
            report_date = datetime.now().date()
        
        print(f"Generating enhanced HTML report for {report_date}")
        
        # Collect all data
        report_data = self._collect_report_data(report_date)
        
        # Prepare template context
        context = {
            'config': REPORT_CONFIG,
            'report_date': report_date if isinstance(report_date, datetime) else datetime.combine(report_date, datetime.min.time()),
            'generated_at': datetime.now(),
            **report_data
        }
        
        # Load and render enhanced template
        template = self.env.get_template('enhanced_main.html')
        html_content = template.render(**context)
        
        # Save enhanced report
        report_filename = f"enhanced_ai_briefing_{report_date.strftime('%Y%m%d')}.html"
        report_path = REPORTS_DIR / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Copy enhanced assets to report directory
        self._copy_enhanced_assets()
        
        # Record report in database with enhanced metadata
        self._record_enhanced_report(report_date, report_path, report_data)
        
        print(f"Enhanced report generated: {report_path}")
        return str(report_path)
    
    def _collect_report_data(self, report_date: datetime) -> Dict[str, Any]:
        """Collect all data for the enhanced report"""
        data = {}
        
        # 1. Intelligence data (existing)
        print("Collecting intelligence data...")
        new_updates = self.db.get_new_updates()
        categorized_updates = self._categorize_updates(new_updates)
        
        # Filter and limit updates per category
        for category in categorized_updates:
            def safe_sort_key(x):
                importance = x.get('importance_score', 0)
                pub_date = x.get('published_date', datetime.min)
                
                if hasattr(pub_date, 'tzinfo') and pub_date.tzinfo is not None:
                    pub_date = pub_date.replace(tzinfo=None)
                
                return (importance, pub_date)
            
            categorized_updates[category].sort(key=safe_sort_key, reverse=True)
            max_items = REPORT_CONFIG['max_items_per_category']
            categorized_updates[category] = categorized_updates[category][:max_items]
        
        data.update({
            'categories': categorized_updates,
            'category_info': CONTENT_CATEGORIES,
            'total_updates': len(new_updates)
        })
        
        # 2. Project status data
        print("Scanning local projects...")
        try:
            projects = self.project_scanner.scan_projects(max_depth=3)
            project_summary = self._generate_project_summary(projects)
            
            data.update({
                'projects': projects,
                'project_summary': project_summary
            })
        except Exception as e:
            print(f"Error scanning projects: {e}")
            data.update({
                'projects': [],
                'project_summary': {}
            })
        
        # 3. Installation data
        print("Detecting installable items...")
        try:
            installable_items = self.installation_manager.detect_installable_items(new_updates)
            installation_categories = self._group_installable_items(installable_items)
            
            data.update({
                'installable_items': installable_items,
                'installation_categories': installation_categories
            })
        except Exception as e:
            print(f"Error detecting installable items: {e}")
            data.update({
                'installable_items': [],
                'installation_categories': {}
            })
        
        # 4. System health data
        print("Gathering system health metrics...")
        try:
            system_health = self._gather_system_health()
            
            data.update({
                'system_health': system_health
            })
        except Exception as e:
            print(f"Error gathering system health: {e}")
            data.update({
                'system_health': {
                    'overall_health': 'unknown',
                    'metrics': {},
                    'recommendations': []
                }
            })
        
        return data
    
    def _categorize_updates(self, updates: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize updates based on content (from original generator)"""
        categorized = {category: [] for category in CONTENT_CATEGORIES.keys()}
        categorized['other'] = []
        
        for update in updates:
            # Parse metadata if it's a JSON string
            if isinstance(update.get('metadata'), str):
                try:
                    update['metadata'] = json.loads(update['metadata'])
                except:
                    pass
            
            # Ensure published_date is a datetime object
            if isinstance(update.get('published_date'), str):
                try:
                    pub_date = datetime.fromisoformat(update['published_date'])
                    if hasattr(pub_date, 'tzinfo') and pub_date.tzinfo is not None:
                        pub_date = pub_date.replace(tzinfo=None)
                    update['published_date'] = pub_date
                except:
                    update['published_date'] = datetime.now()
            elif not update.get('published_date'):
                update['published_date'] = datetime.now()
            else:
                pub_date = update['published_date']
                if hasattr(pub_date, 'tzinfo') and pub_date.tzinfo is not None:
                    update['published_date'] = pub_date.replace(tzinfo=None)
            
            title_lower = update['title'].lower()
            content_lower = (update.get('content') or '').lower()
            combined_text = f"{title_lower} {content_lower}"
            
            categorized_flag = False
            
            # Check each category
            for category_key, category_info in CONTENT_CATEGORIES.items():
                keywords = category_info['keywords']
                
                if any(keyword.lower() in combined_text for keyword in keywords):
                    update['category'] = category_key
                    categorized[category_key].append(update)
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                update['category'] = 'other'
                categorized['other'].append(update)
        
        return categorized
    
    def _generate_project_summary(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate project summary statistics"""
        if not projects:
            return {
                'total_projects': 0,
                'average_health_score': 0,
                'project_types': {},
                'health_distribution': {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0},
                'needs_attention': 0,
                'total_todos': 0,
                'git_repos': 0
            }
        
        total_projects = len(projects)
        avg_health = sum(p['health_score'] for p in projects) / total_projects
        
        # Count by type
        types = {}
        for project in projects:
            project_type = project['type']
            types[project_type] = types.get(project_type, 0) + 1
        
        # Health distribution
        health_categories = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        for project in projects:
            score = project['health_score']
            if score >= 90:
                health_categories['excellent'] += 1
            elif score >= 75:
                health_categories['good'] += 1
            elif score >= 50:
                health_categories['fair'] += 1
            else:
                health_categories['poor'] += 1
        
        return {
            'total_projects': total_projects,
            'average_health_score': round(avg_health, 1),
            'project_types': types,
            'health_distribution': health_categories,
            'needs_attention': len([p for p in projects if p['health_score'] < 70]),
            'total_todos': sum(len(p['todos']) for p in projects),
            'git_repos': len([p for p in projects if p['git_info']['is_repo']])
        }
    
    def _group_installable_items(self, items: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Group installable items by category"""
        categories = {}
        for item in items:
            # Convert InstallationItem to dict if needed
            if hasattr(item, '__dict__'):
                item_dict = item.__dict__
            else:
                item_dict = item
            
            category = item_dict.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(item_dict)
        
        return categories
    
    def _gather_system_health(self) -> Dict[str, Any]:
        """Gather system health metrics and recommendations"""
        health_data = {
            'overall_health': 'good',
            'uptime_hours': 24.0,  # Simplified for demo
            'metrics': {},
            'recommendations': []
        }
        
        try:
            # Database metrics
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Recent updates count
                cursor.execute("""
                    SELECT COUNT(*) as count FROM updates 
                    WHERE published_date >= datetime('now', '-1 day')
                """)
                recent_updates = cursor.fetchone()['count']
                
                # Cache statistics
                cursor.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN expires_at > datetime('now') THEN 1 ELSE 0 END) as valid
                    FROM cache
                """)
                cache_stats = cursor.fetchone()
                
                health_data['metrics'].update({
                    'recent_updates': recent_updates,
                    'cache_hit_rate': (cache_stats['valid'] / cache_stats['total'] * 100) if cache_stats['total'] > 0 else 0,
                    'disk_usage_mb': self._get_disk_usage(),
                    'installation_success_rate': 85.0  # Could be calculated from installation history
                })
            
            # Generate recommendations
            recommendations = []
            
            if recent_updates < 5:
                recommendations.append({
                    'priority': 'low',
                    'category': 'data_collection',
                    'title': 'Low Update Volume',
                    'description': f'Only {recent_updates} updates in the last 24 hours.',
                    'action': 'Consider adding more data sources'
                })
            
            if health_data['metrics']['cache_hit_rate'] < 50:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'performance',
                    'title': 'Poor Cache Performance',
                    'description': f'Cache hit rate is {health_data["metrics"]["cache_hit_rate"]:.1f}%.',
                    'action': 'Review cache expiration settings'
                })
            
            health_data['recommendations'] = recommendations
            
        except Exception as e:
            print(f"Error gathering system health: {e}")
            health_data['overall_health'] = 'error'
        
        return health_data
    
    def _get_disk_usage(self) -> float:
        """Calculate disk usage in MB"""
        try:
            total_size = 0
            for path in [REPORTS_DIR, BASE_DIR / 'logs', BASE_DIR / 'cache']:
                if path.exists():
                    for file_path in path.rglob('*'):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
            return round(total_size / (1024 * 1024), 2)
        except:
            return 0
    
    def _copy_enhanced_assets(self):
        """Copy enhanced CSS and JS files to reports directory"""
        import shutil
        
        assets = {
            'enhanced_styles.css': 'enhanced_styles.css',
            'enhanced_script.js': 'enhanced_script.js'
        }
        
        for source_name, dest_name in assets.items():
            source_path = self.template_dir / source_name
            dest_path = REPORTS_DIR / dest_name
            
            if source_path.exists():
                try:
                    shutil.copy2(source_path, dest_path)
                except Exception as e:
                    print(f"Warning: Could not copy {source_name}: {e}")
    
    def _record_enhanced_report(self, report_date: datetime, report_path: Path, report_data: Dict[str, Any]):
        """Record enhanced report in database with metadata"""
        metadata = {
            'enhanced': True,
            'projects_scanned': len(report_data.get('projects', [])),
            'installable_items': len(report_data.get('installable_items', [])),
            'system_health': report_data.get('system_health', {}).get('overall_health', 'unknown'),
            'categories': len([cat for cat, items in report_data.get('categories', {}).items() if items])
        }
        
        self.db.add_report(
            datetime.combine(report_date, datetime.min.time()) if not isinstance(report_date, datetime) else report_date,
            str(report_path),
            report_data.get('total_updates', 0),
            metadata
        )
    
    def _from_json_filter(self, value):
        """Jinja2 filter to parse JSON strings"""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return {}
        return value if isinstance(value, dict) else {}


# Backwards compatibility - update existing HTML generator to use enhanced version
class HTMLGenerator(EnhancedHTMLGenerator):
    """Backwards compatible HTML generator that uses enhanced features"""
    
    def generate_report(self, report_date: datetime = None) -> str:
        """Generate report using enhanced generator"""
        return self.generate_enhanced_report(report_date)


def main():
    """Test the enhanced HTML generator"""
    generator = EnhancedHTMLGenerator()
    report_path = generator.generate_enhanced_report()
    print(f"Enhanced test report generated at: {report_path}")


if __name__ == "__main__":
    main()