#!/Users/daniel/daily-intelligence-briefing/venv/bin/python
"""
Main entry point for the daily intelligence briefing system
"""
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import traceback

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import REPORT_CONFIG
from data_collector import DataCollector
from html_generator import HTMLGenerator
from scheduler import BrowserManager, NotificationManager
from database import DatabaseManager


class BriefingOrchestrator:
    """Main orchestrator for the briefing system"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.html_generator = HTMLGenerator()
        self.notification_manager = NotificationManager()
        self.browser_manager = BrowserManager()
    
    async def run_full_briefing(self, force: bool = False) -> bool:
        """Run the complete briefing generation process"""
        try:
            print(f"Starting intelligence briefing generation at {datetime.now()}")
            
            # Check if we've already generated today's report (unless forced)
            if not force:
                today = datetime.now().date()
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) as count FROM reports 
                        WHERE report_date = ?
                    """, (today,))
                    result = cursor.fetchone()
                    
                    if result and result['count'] > 0:
                        print("Report already generated today. Use --force to regenerate.")
                        return True
            
            # Step 1: Collect data from all sources
            print("Phase 1: Data Collection")
            async with DataCollector() as collector:
                categorized_updates = await collector.collect_all_data()
            
            total_updates = sum(len(updates) for updates in categorized_updates.values())
            print(f"Collected {total_updates} updates across {len(categorized_updates)} categories")
            
            # Step 2: Generate HTML report
            print("Phase 2: HTML Report Generation")
            report_path = self.html_generator.generate_report()
            
            print(f"Report generated successfully: {report_path}")
            
            # Step 3: Clean up old reports (keep last 30 days)
            self._cleanup_old_reports()
            
            # Step 4: Clean expired cache
            expired_count = self.db.clean_expired_cache()
            if expired_count > 0:
                print(f"Cleaned {expired_count} expired cache entries")
            
            # Step 5: Send notification
            self.notification_manager.notify_report_ready(report_path)
            
            # Step 6: Auto-open browser if configured and within time window
            if REPORT_CONFIG.get('auto_open_browser', True):
                if self.browser_manager.should_auto_open() or force:
                    self.browser_manager.open_latest_report()
            
            print("Briefing generation completed successfully!")
            return True
            
        except Exception as e:
            error_msg = f"Error generating briefing: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            
            self.notification_manager.notify_error(error_msg)
            return False
    
    def _cleanup_old_reports(self) -> None:
        """Clean up old report files (keep last 30 days)"""
        try:
            from config import REPORTS_DIR
            cutoff_date = datetime.now() - timedelta(days=30)
            
            report_files = list(REPORTS_DIR.glob("ai_briefing_*.html"))
            removed_count = 0
            
            for report_file in report_files:
                # Extract date from filename
                try:
                    date_str = report_file.stem.split('_')[-1]  # ai_briefing_YYYYMMDD
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
                    print(f"Error processing {report_file}: {e}")
                    continue
            
            if removed_count > 0:
                print(f"Cleaned up {removed_count} old report files")
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def get_system_status(self) -> dict:
        """Get system status information"""
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
                'error': str(e)
            }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='AI Intelligence Briefing System')
    parser.add_argument('--force', action='store_true', 
                       help='Force generation even if report exists today')
    parser.add_argument('--status', action='store_true',
                       help='Show system status information')
    parser.add_argument('--open', action='store_true',
                       help='Open the latest report in browser')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up old reports and cache')
    
    args = parser.parse_args()
    
    orchestrator = BriefingOrchestrator()
    
    if args.status:
        # Show status
        status = orchestrator.get_system_status()
        print("\n=== AI Intelligence Briefing System Status ===")
        print(f"Status: {status['status'].upper()}")
        
        if status['status'] == 'healthy':
            print(f"Last Report: {status['last_report'] or 'Never'}")
            print(f"Reports (30 days): {status['reports_last_30_days']}")
            print(f"Database: {status['database_path']}")
            print(f"Reports Directory: {status['reports_directory']}")
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
        print(f"Cleanup completed. Removed {expired} expired cache entries.")
        return
    
    # Run the briefing
    success = asyncio.run(orchestrator.run_full_briefing(force=args.force))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()