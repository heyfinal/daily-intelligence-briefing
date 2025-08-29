#!/Users/daniel/daily-intelligence-briefing/venv/bin/python
"""
Enhanced AI Intelligence Briefing System - Main Entry Point
Integrates all enhanced features including project scanning, installation management, and web API
"""
import sys
import asyncio
import argparse
import threading
import signal
import time
from pathlib import Path
from datetime import datetime, timedelta
import traceback
import logging

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import REPORT_CONFIG
from data_collector import DataCollector
from enhanced_html_generator import EnhancedHTMLGenerator
from scheduler import BrowserManager, NotificationManager
from database import DatabaseManager
from project_scanner import ProjectScanner
from installation_manager import InstallationManager
from web_api import WebAPI


class EnhancedBriefingOrchestrator:
    """Enhanced orchestrator with all new features"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.html_generator = EnhancedHTMLGenerator()
        self.notification_manager = NotificationManager()
        self.browser_manager = BrowserManager()
        self.project_scanner = ProjectScanner()
        self.installation_manager = InstallationManager()
        self.web_api = None
        self.web_api_thread = None
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self._running = True
    
    def _setup_logger(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger('enhanced_briefing')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # File handler
            log_path = Path(__file__).parent / 'logs' / 'enhanced_briefing.log'
            log_path.parent.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._running = False
        
        if self.web_api_thread and self.web_api_thread.is_alive():
            self.logger.info("Stopping web API server...")
            # In a real implementation, we'd have a proper shutdown mechanism
            
        sys.exit(0)
    
    async def run_enhanced_briefing(self, force: bool = False, 
                                  include_projects: bool = True,
                                  include_installations: bool = True,
                                  start_web_api: bool = False) -> bool:
        """Run the complete enhanced briefing generation process"""
        start_time = datetime.now()
        self.logger.info(f"Starting enhanced intelligence briefing at {start_time}")
        
        try:
            # Check if we've already generated today's enhanced report (unless forced)
            if not force and self._report_exists_today():
                self.logger.info("Enhanced report already generated today. Use --force to regenerate.")
                return True
            
            # Phase 1: Data Collection
            self.logger.info("Phase 1: Intelligence Data Collection")
            async with DataCollector() as collector:
                categorized_updates = await collector.collect_all_data()
            
            total_updates = sum(len(updates) for updates in categorized_updates.values())
            self.logger.info(f"Collected {total_updates} updates across {len(categorized_updates)} categories")
            
            # Phase 2: Enhanced Analysis (Parallel Processing)
            self.logger.info("Phase 2: Enhanced Analysis (Project Scanning & Package Detection)")
            
            analysis_tasks = []
            
            if include_projects:
                analysis_tasks.append(self._scan_projects())
            
            if include_installations:
                # Get updates for installation detection
                all_updates = []
                for updates_list in categorized_updates.values():
                    all_updates.extend(updates_list)
                analysis_tasks.append(self._detect_installable_items(all_updates))
            
            # Run analysis tasks in parallel
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process analysis results
            projects_data = []
            installable_items = []
            
            for i, result in enumerate(analysis_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Analysis task {i} failed: {result}")
                elif include_projects and i == 0:
                    projects_data = result
                elif include_installations and i == (1 if include_projects else 0):
                    installable_items = result
            
            # Phase 3: Enhanced HTML Report Generation
            self.logger.info("Phase 3: Enhanced Report Generation")
            report_path = self.html_generator.generate_enhanced_report()
            
            # Phase 4: System Maintenance
            self.logger.info("Phase 4: System Maintenance")
            await self._run_maintenance_tasks()
            
            # Phase 5: Start Web API if requested
            if start_web_api:
                self._start_web_api()
            
            # Phase 6: Notifications and Browser Opening
            self.logger.info("Phase 6: Notifications")
            self.notification_manager.notify_report_ready(report_path)
            
            if REPORT_CONFIG.get('auto_open_browser', True):
                if self.browser_manager.should_auto_open() or force:
                    self.browser_manager.open_latest_report()
            
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Enhanced briefing completed successfully in {duration:.1f}s!")
            
            # Log summary statistics
            self._log_summary_stats(total_updates, len(projects_data), len(installable_items))
            
            return True
            
        except Exception as e:
            error_msg = f"Error generating enhanced briefing: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            
            self.notification_manager.notify_error(error_msg)
            return False
    
    async def _scan_projects(self) -> list:
        """Scan local projects asynchronously"""
        self.logger.info("Scanning local projects...")
        
        def scan_sync():
            return self.project_scanner.scan_projects(max_depth=3)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        projects = await loop.run_in_executor(None, scan_sync)
        
        self.logger.info(f"Found {len(projects)} local projects")
        return projects
    
    async def _detect_installable_items(self, updates: list) -> list:
        """Detect installable items asynchronously"""
        self.logger.info("Detecting installable packages...")
        
        def detect_sync():
            return self.installation_manager.detect_installable_items(updates)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        items = await loop.run_in_executor(None, detect_sync)
        
        self.logger.info(f"Detected {len(items)} installable items")
        return items
    
    async def _run_maintenance_tasks(self):
        """Run system maintenance tasks"""
        self.logger.info("Running maintenance tasks...")
        
        # Clean up old reports (keep last 30 days)
        self._cleanup_old_reports()
        
        # Clean expired cache
        expired_count = self.db.clean_expired_cache()
        if expired_count > 0:
            self.logger.info(f"Cleaned {expired_count} expired cache entries")
        
        # Clean up old installation logs
        self.installation_manager.cleanup_old_logs(days_to_keep=30)
        
        # Database optimization (vacuum)
        with self.db.get_connection() as conn:
            conn.execute('VACUUM')
            self.logger.info("Database optimized")
    
    def _start_web_api(self):
        """Start web API server in background thread"""
        self.logger.info("Starting web API server...")
        
        def run_web_api():
            try:
                self.web_api = WebAPI()
                port = REPORT_CONFIG.get('enhanced_features', {}).get('api_port', 5000)
                self.web_api.run(host='127.0.0.1', port=port, debug=False)
            except Exception as e:
                self.logger.error(f"Web API failed to start: {e}")
        
        self.web_api_thread = threading.Thread(target=run_web_api, daemon=True)
        self.web_api_thread.start()
        
        # Give it a moment to start
        time.sleep(2)
        
        if self.web_api_thread.is_alive():
            self.logger.info("Web API server started successfully")
        else:
            self.logger.error("Web API server failed to start")
    
    def _report_exists_today(self) -> bool:
        """Check if enhanced report already exists for today"""
        today = datetime.now().date()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count FROM reports 
                WHERE report_date = ? AND (metadata LIKE '%"enhanced": true%' OR json_extract(metadata, '$.enhanced') = 1)
            """, (today,))
            result = cursor.fetchone()
            return result and result['count'] > 0
    
    def _cleanup_old_reports(self) -> None:
        """Clean up old report files (keep last 30 days)"""
        try:
            from config import REPORTS_DIR
            cutoff_date = datetime.now() - timedelta(days=30)
            
            report_files = list(REPORTS_DIR.glob("*ai_briefing_*.html"))
            removed_count = 0
            
            for report_file in report_files:
                try:
                    # Extract date from filename
                    date_str = report_file.stem.split('_')[-1]
                    file_date = datetime.strptime(date_str, '%Y%m%d')
                    
                    if file_date < cutoff_date:
                        report_file.unlink()
                        removed_count += 1
                        
                        # Also remove from database
                        with self.db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                DELETE FROM reports 
                                WHERE file_path = ?
                            """, (str(report_file),))
                
                except Exception as e:
                    self.logger.error(f"Error processing {report_file}: {e}")
                    continue
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old report files")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def _log_summary_stats(self, updates_count: int, projects_count: int, installable_count: int):
        """Log summary statistics"""
        self.logger.info("=== Enhanced Briefing Summary ===")
        self.logger.info(f"Intelligence Updates: {updates_count}")
        self.logger.info(f"Projects Scanned: {projects_count}")
        self.logger.info(f"Installable Items Detected: {installable_count}")
        
        # Database stats
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM updates WHERE processed = 0")
            unprocessed = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM cache WHERE expires_at > datetime('now')")
            valid_cache = cursor.fetchone()['count']
            
            self.logger.info(f"Unprocessed Updates: {unprocessed}")
            self.logger.info(f"Valid Cache Entries: {valid_cache}")
        
        self.logger.info("==================================")
    
    def get_enhanced_status(self) -> dict:
        """Get enhanced system status information"""
        try:
            # Base status
            base_status = self.get_system_status()
            
            # Enhanced status additions
            enhanced_status = {
                'enhanced_features': {
                    'project_scanning': True,
                    'installation_management': True,
                    'web_api': self.web_api_thread is not None and self.web_api_thread.is_alive(),
                    'system_health_monitoring': True
                }
            }
            
            # Project statistics
            try:
                recent_projects = self.project_scanner.scan_projects(max_depth=2)
                enhanced_status['projects'] = {
                    'total_scanned': len(recent_projects),
                    'average_health': sum(p['health_score'] for p in recent_projects) / len(recent_projects) if recent_projects else 0,
                    'needs_attention': len([p for p in recent_projects if p['health_score'] < 70])
                }
            except Exception as e:
                self.logger.error(f"Error getting project stats: {e}")
                enhanced_status['projects'] = {'error': str(e)}
            
            # Installation statistics
            try:
                install_history = self.installation_manager.get_installation_history(50)
                if install_history:
                    success_rate = sum(1 for h in install_history if h['success']) / len(install_history) * 100
                    enhanced_status['installations'] = {
                        'total_attempts': len(install_history),
                        'success_rate': success_rate,
                        'recent_failures': len([h for h in install_history[:10] if not h['success']])
                    }
                else:
                    enhanced_status['installations'] = {
                        'total_attempts': 0,
                        'success_rate': 0,
                        'recent_failures': 0
                    }
            except Exception as e:
                self.logger.error(f"Error getting installation stats: {e}")
                enhanced_status['installations'] = {'error': str(e)}
            
            # Merge with base status
            base_status.update(enhanced_status)
            return base_status
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'enhanced': True
            }
    
    def get_system_status(self) -> dict:
        """Get basic system status information (from original)"""
        try:
            # Database stats
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Count updates by source
                cursor.execute("""
                    SELECT source, COUNT(*) as count 
                    FROM updates 
                    WHERE published_date >= date('now', '-7 days')
                    GROUP BY source
                """)
                source_counts = dict(cursor.fetchall())
                
                # Count reports
                cursor.execute("""
                    SELECT COUNT(*) as count FROM reports
                    WHERE report_date >= date('now', '-30 days')
                """)
                report_count = cursor.fetchone()['count']
                
                # Last report date
                cursor.execute("""
                    SELECT MAX(report_date) as last_date FROM reports
                """)
                last_report = cursor.fetchone()['last_date']
                
                # Cache stats
                cursor.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN expires_at > datetime('now') THEN 1 ELSE 0 END) as valid
                    FROM cache
                """)
                cache_stats = cursor.fetchone()
            
            return {
                'status': 'healthy',
                'enhanced': True,
                'last_report': last_report,
                'reports_last_30_days': report_count,
                'updates_last_7_days': source_counts,
                'cache_entries': {
                    'total': cache_stats['total'],
                    'valid': cache_stats['valid']
                },
                'database_path': str(self.db.db_path),
                'reports_directory': str(Path(__file__).parent / 'reports')
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'enhanced': True
            }


def main():
    """Enhanced main entry point"""
    parser = argparse.ArgumentParser(
        description='Enhanced AI Intelligence Briefing System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_enhanced_briefing.py --enhanced                    # Full enhanced report
  python run_enhanced_briefing.py --enhanced --web-api         # With web API
  python run_enhanced_briefing.py --status                     # System status
  python run_enhanced_briefing.py --enhanced --no-projects     # Skip project scanning
        """
    )
    
    parser.add_argument('--enhanced', action='store_true', default=True,
                       help='Generate enhanced report (default)')
    parser.add_argument('--force', action='store_true', 
                       help='Force generation even if report exists today')
    parser.add_argument('--status', action='store_true',
                       help='Show enhanced system status information')
    parser.add_argument('--open', action='store_true',
                       help='Open the latest report in browser')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up old reports and cache')
    parser.add_argument('--web-api', action='store_true',
                       help='Start web API server alongside report generation')
    parser.add_argument('--no-projects', action='store_true',
                       help='Skip project scanning (faster generation)')
    parser.add_argument('--no-installations', action='store_true',
                       help='Skip installation detection')
    parser.add_argument('--scan-depth', type=int, default=3, metavar='N',
                       help='Project scanning depth (default: 3)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    orchestrator = EnhancedBriefingOrchestrator()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        orchestrator.logger.setLevel(logging.DEBUG)
    
    if args.status:
        # Show enhanced status
        status = orchestrator.get_enhanced_status()
        print("\n=== Enhanced AI Intelligence Briefing System Status ===")
        print(f"Status: {status['status'].upper()}")
        
        if status['status'] == 'healthy':
            print(f"Last Report: {status['last_report'] or 'Never'}")
            print(f"Reports (30 days): {status['reports_last_30_days']}")
            print(f"Database: {status['database_path']}")
            print(f"Reports Directory: {status['reports_directory']}")
            
            print("\n=== Enhanced Features ===")
            features = status.get('enhanced_features', {})
            for feature, enabled in features.items():
                status_icon = "✅" if enabled else "❌"
                print(f"  {status_icon} {feature.replace('_', ' ').title()}")
            
            if 'projects' in status:
                print("\n=== Project Statistics ===")
                projects = status['projects']
                if 'error' not in projects:
                    print(f"  Total Projects: {projects['total_scanned']}")
                    print(f"  Average Health: {projects['average_health']:.1f}/100")
                    print(f"  Need Attention: {projects['needs_attention']}")
                else:
                    print(f"  Error: {projects['error']}")
            
            if 'installations' in status:
                print("\n=== Installation Statistics ===")
                installs = status['installations']
                if 'error' not in installs:
                    print(f"  Total Attempts: {installs['total_attempts']}")
                    print(f"  Success Rate: {installs['success_rate']:.1f}%")
                    print(f"  Recent Failures: {installs['recent_failures']}")
                else:
                    print(f"  Error: {installs['error']}")
            
            print("\nUpdates (7 days):")
            for source, count in status['updates_last_7_days'].items():
                print(f"  {source}: {count}")
            print(f"\nCache: {status['cache_entries']['valid']}/{status['cache_entries']['total']} valid entries")
        else:
            print(f"Error: {status.get('error', 'Unknown error')}")
        
        return
    
    if args.open:
        # Open latest report
        orchestrator.browser_manager.open_latest_report()
        return
    
    if args.cleanup:
        # Manual cleanup
        orchestrator._cleanup_old_reports()
        expired = orchestrator.db.clean_expired_cache()
        orchestrator.installation_manager.cleanup_old_logs()
        print(f"Cleanup completed. Removed {expired} expired cache entries.")
        return
    
    # Run the enhanced briefing
    success = asyncio.run(orchestrator.run_enhanced_briefing(
        force=args.force,
        include_projects=not args.no_projects,
        include_installations=not args.no_installations,
        start_web_api=args.web_api
    ))
    
    if args.web_api and success:
        print("\n🌐 Web API is running at: http://127.0.0.1:5000/api/")
        print("Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()