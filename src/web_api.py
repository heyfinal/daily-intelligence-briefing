"""
Web API for the enhanced daily intelligence briefing system
Handles installation requests and project status queries
"""
from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import threading
import time
from dataclasses import asdict

from config import BASE_DIR, REPORTS_DIR
from installation_manager import InstallationManager, InstallationItem
from project_scanner import ProjectScanner
from database import DatabaseManager


class WebAPI:
    """Flask web API for installation management and project status"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.installation_manager = InstallationManager()
        self.project_scanner = ProjectScanner()
        self.db = DatabaseManager()
        
        self.logger = self._setup_logger()
        
        # Setup routes
        self._setup_routes()
        
        # WebSocket-like progress tracking (using polling)
        self.progress_subscribers = {}
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for web API"""
        logger = logging.getLogger('web_api')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler(BASE_DIR / 'logs' / 'web_api.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0'
            })
        
        @self.app.route('/api/installable-items', methods=['GET'])
        def get_installable_items():
            """Get list of installable items from latest intelligence data"""
            try:
                # Get recent updates from database
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT title, content, url, source, published_date, metadata
                        FROM updates 
                        WHERE published_date >= date('now', '-1 days')
                        ORDER BY published_date DESC
                        LIMIT 100
                    """)
                    updates = [dict(row) for row in cursor.fetchall()]
                
                # Detect installable items
                items = self.installation_manager.detect_installable_items(updates)
                
                # Convert to JSON-serializable format
                items_dict = [asdict(item) for item in items]
                
                return jsonify({
                    'items': items_dict,
                    'total_count': len(items_dict),
                    'categories': self._group_by_category(items_dict)
                })
                
            except Exception as e:
                self.logger.error(f"Error getting installable items: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/install', methods=['POST'])
        def install_packages():
            """Install selected packages"""
            try:
                data = request.get_json()
                if not data or 'items' not in data:
                    return jsonify({'error': 'No items provided'}), 400
                
                # Convert dict items back to InstallationItem objects
                items = []
                for item_data in data['items']:
                    item = InstallationItem(**item_data)
                    items.append(item)
                
                # Queue for installation
                batch_id, rejected_items = self.installation_manager.queue_installations(items)
                
                if batch_id:
                    self.logger.info(f"Queued {len(items)} items for installation (batch: {batch_id})")
                    return jsonify({
                        'batch_id': batch_id,
                        'queued_count': len(items),
                        'rejected_items': rejected_items,
                        'status': 'queued'
                    })
                else:
                    return jsonify({
                        'error': 'No valid items to install',
                        'rejected_items': rejected_items
                    }), 400
                    
            except Exception as e:
                self.logger.error(f"Error installing packages: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/installation-progress/<batch_id>', methods=['GET'])
        def get_installation_progress(batch_id):
            """Get installation progress for a specific batch"""
            try:
                progress = self.installation_manager.get_installation_progress(batch_id)
                return jsonify(progress)
                
            except Exception as e:
                self.logger.error(f"Error getting installation progress: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/installation-progress', methods=['GET'])
        def get_all_installation_progress():
            """Get all installation progress"""
            try:
                progress = self.installation_manager.get_installation_progress()
                return jsonify(progress)
                
            except Exception as e:
                self.logger.error(f"Error getting installation progress: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/installation-history', methods=['GET'])
        def get_installation_history():
            """Get installation history"""
            try:
                limit = request.args.get('limit', 50, type=int)
                history = self.installation_manager.get_installation_history(limit)
                return jsonify({
                    'history': history,
                    'total_count': len(history)
                })
                
            except Exception as e:
                self.logger.error(f"Error getting installation history: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/projects', methods=['GET'])
        def get_project_status():
            """Get local project status"""
            try:
                max_depth = request.args.get('depth', 3, type=int)
                projects = self.project_scanner.scan_projects(max_depth=max_depth)
                
                # Sort by health score and last modified
                projects.sort(key=lambda p: (p['health_score'], p['last_modified']), reverse=True)
                
                return jsonify({
                    'projects': projects,
                    'total_count': len(projects),
                    'summary': self._generate_project_summary(projects)
                })
                
            except Exception as e:
                self.logger.error(f"Error getting project status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/projects/<project_id>/recommendations', methods=['GET'])
        def get_project_recommendations(project_id):
            """Get recommendations for a specific project"""
            try:
                # For now, project_id is a hash of the project path
                # In a real implementation, we'd store projects in a database
                projects = self.project_scanner.scan_projects(max_depth=3)
                
                for project in projects:
                    if project.get('id') == project_id or project['path'].endswith(project_id):
                        return jsonify({
                            'project': project,
                            'recommendations': project['recommendations']
                        })
                
                return jsonify({'error': 'Project not found'}), 404
                
            except Exception as e:
                self.logger.error(f"Error getting project recommendations: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/system-health', methods=['GET'])
        def get_system_health():
            """Get system health and recommendations"""
            try:
                # Get system statistics
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Updates in last 24 hours
                    cursor.execute("""
                        SELECT COUNT(*) as count FROM updates 
                        WHERE published_date >= datetime('now', '-1 day')
                    """)
                    recent_updates = cursor.fetchone()['count']
                    
                    # Cache hit rate
                    cursor.execute("""
                        SELECT COUNT(*) as total,
                               SUM(CASE WHEN expires_at > datetime('now') THEN 1 ELSE 0 END) as valid
                        FROM cache
                    """)
                    cache_stats = cursor.fetchone()
                
                # Installation statistics
                installation_history = self.installation_manager.get_installation_history(100)
                recent_installations = [h for h in installation_history 
                                      if datetime.fromisoformat(h['timestamp']) > 
                                      datetime.now().replace(hour=0, minute=0, second=0)]
                
                success_rate = 0
                if installation_history:
                    successes = sum(1 for h in installation_history if h['success'])
                    success_rate = (successes / len(installation_history)) * 100
                
                health_data = {
                    'overall_health': 'good',  # Could be calculated based on various factors
                    'uptime_hours': self._get_uptime_hours(),
                    'recent_updates': recent_updates,
                    'cache_hit_rate': (cache_stats['valid'] / cache_stats['total'] * 100) if cache_stats['total'] > 0 else 0,
                    'installation_success_rate': success_rate,
                    'recent_installations': len(recent_installations),
                    'disk_usage_mb': self._get_disk_usage(),
                    'recommendations': self._generate_system_recommendations(
                        recent_updates, cache_stats, installation_history
                    )
                }
                
                return jsonify(health_data)
                
            except Exception as e:
                self.logger.error(f"Error getting system health: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/latest', methods=['GET'])
        def get_latest_report():
            """Get the latest HTML report"""
            try:
                # Find latest report file
                report_files = list(REPORTS_DIR.glob('ai_briefing_*.html'))
                if not report_files:
                    return jsonify({'error': 'No reports found'}), 404
                
                latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
                return send_file(latest_report)
                
            except Exception as e:
                self.logger.error(f"Error serving latest report: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _group_by_category(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group items by category"""
        categories = {}
        for item in items:
            category = item.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        return categories
    
    def _generate_project_summary(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for projects"""
        if not projects:
            return {}
        
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
    
    def _generate_system_recommendations(self, recent_updates: int, cache_stats: Dict, 
                                       installation_history: List[Dict]) -> List[Dict[str, Any]]:
        """Generate system-level recommendations"""
        recommendations = []
        
        # Update frequency recommendations
        if recent_updates < 5:
            recommendations.append({
                'priority': 'low',
                'category': 'data_collection',
                'title': 'Low Update Volume',
                'description': f'Only {recent_updates} updates in the last 24 hours. Consider adding more data sources.',
                'action': 'Review and expand data source configuration'
            })
        
        # Cache performance
        cache_hit_rate = (cache_stats['valid'] / cache_stats['total'] * 100) if cache_stats['total'] > 0 else 0
        if cache_hit_rate < 50:
            recommendations.append({
                'priority': 'medium',
                'category': 'performance',
                'title': 'Poor Cache Performance',
                'description': f'Cache hit rate is only {cache_hit_rate:.1f}%. Consider tuning cache settings.',
                'action': 'Review cache expiration times and cleanup policies'
            })
        
        # Installation success rate
        if installation_history:
            success_rate = sum(1 for h in installation_history if h['success']) / len(installation_history) * 100
            if success_rate < 80:
                recommendations.append({
                    'priority': 'high',
                    'category': 'installation',
                    'title': 'Low Installation Success Rate',
                    'description': f'Only {success_rate:.1f}% of installations succeed. Check system dependencies.',
                    'action': 'Review failed installations and resolve common issues'
                })
        
        # Disk usage
        disk_usage = self._get_disk_usage()
        if disk_usage > 500:  # > 500MB
            recommendations.append({
                'priority': 'medium',
                'category': 'maintenance',
                'title': 'High Disk Usage',
                'description': f'System using {disk_usage}MB. Consider cleanup.',
                'action': 'Run cleanup routine to remove old reports and logs'
            })
        
        return recommendations
    
    def _get_uptime_hours(self) -> float:
        """Get system uptime in hours (simplified)"""
        # This is a simplified implementation
        # In practice, you'd track when the system started
        return 24.0  # Assume 24 hours for demo
    
    def _get_disk_usage(self) -> float:
        """Get disk usage in MB"""
        try:
            total_size = 0
            for path in [BASE_DIR / 'reports', BASE_DIR / 'logs', BASE_DIR / 'cache']:
                if path.exists():
                    for file_path in path.rglob('*'):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
            return round(total_size / (1024 * 1024), 2)
        except:
            return 0
    
    def run(self, host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
        """Run the Flask web server"""
        self.logger.info(f"Starting web API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    """Run the web API server"""
    api = WebAPI()
    api.run(debug=True)


if __name__ == "__main__":
    main()