"""
Database management for intelligence briefing system
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
from contextlib import contextmanager

from config import DB_PATH, CACHE_EXPIRY_HOURS


class DatabaseManager:
    """Manages SQLite database for historical tracking and caching"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Updates table - stores all collected updates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS updates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    url TEXT,
                    category TEXT,
                    importance_score REAL DEFAULT 0,
                    published_date DATETIME,
                    collected_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    content_hash TEXT UNIQUE,
                    metadata TEXT,
                    UNIQUE(source, source_id)
                )
            """)
            
            # Cache table - stores API responses
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL
                )
            """)
            
            # Reports table - tracks generated reports
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date DATE UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    update_count INTEGER DEFAULT 0,
                    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Rate limiting table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    last_call DATETIME DEFAULT CURRENT_TIMESTAMP,
                    call_count INTEGER DEFAULT 0,
                    reset_time DATETIME
                )
            """)
            
            # Create indices for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_updates_date ON updates(published_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_updates_category ON updates(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON cache(cache_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
    
    def add_update(self, source: str, source_id: str, title: str, 
                   content: str = None, url: str = None, category: str = None,
                   published_date: datetime = None, metadata: Dict = None) -> bool:
        """Add a new update to the database"""
        # Generate content hash to avoid duplicates
        content_hash = hashlib.sha256(
            f"{source}{source_id}{title}".encode()
        ).hexdigest()
        
        # Convert datetime to string for storage
        if published_date:
            published_date_str = published_date.isoformat()
        else:
            published_date_str = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO updates 
                    (source, source_id, title, content, url, category, 
                     published_date, content_hash, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    source, source_id, title, content, url, category,
                    published_date_str,
                    content_hash,
                    json.dumps(metadata, default=str) if metadata else None
                ))
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                # Update already exists
                return False
    
    def get_updates_since(self, since_date: datetime, 
                          category: str = None) -> List[Dict]:
        """Get all updates since a specific date"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM updates 
                WHERE published_date >= ?
            """
            params = [since_date.isoformat()]
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY published_date DESC, importance_score DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert string dates back to datetime objects
            updates = []
            for row in rows:
                update = dict(row)
                if update.get('published_date'):
                    try:
                        update['published_date'] = datetime.fromisoformat(update['published_date'])
                    except:
                        update['published_date'] = datetime.now()
                updates.append(update)
            
            return updates
    
    def get_new_updates(self, last_report_date: datetime = None) -> List[Dict]:
        """Get updates that haven't been included in a report yet"""
        if not last_report_date:
            # Get the date of the last report
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MAX(report_date) as last_date FROM reports
                """)
                result = cursor.fetchone()
                if result and result['last_date']:
                    last_report_date = datetime.fromisoformat(result['last_date'])
                else:
                    last_report_date = datetime.now() - timedelta(days=1)
        
        return self.get_updates_since(last_report_date)
    
    def get_cache(self, cache_key: str) -> Optional[Any]:
        """Get cached data if not expired"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data FROM cache 
                WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
            """, (cache_key,))
            
            result = cursor.fetchone()
            if result:
                return json.loads(result['data'])
            return None
    
    def set_cache(self, cache_key: str, data: Any, 
                  expiry_hours: int = None) -> None:
        """Set cache data with expiration"""
        if expiry_hours is None:
            expiry_hours = CACHE_EXPIRY_HOURS
        
        expires_at = datetime.now() + timedelta(hours=expiry_hours)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cache (cache_key, data, expires_at)
                VALUES (?, ?, ?)
            """, (cache_key, json.dumps(data, default=str), expires_at.isoformat()))
    
    def clean_expired_cache(self) -> int:
        """Remove expired cache entries"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM cache WHERE expires_at <= CURRENT_TIMESTAMP
            """)
            return cursor.rowcount
    
    def add_report(self, report_date: datetime, file_path: str, 
                   update_count: int, metadata: Dict = None) -> None:
        """Record a generated report"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO reports 
                (report_date, file_path, update_count, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                report_date.date().isoformat() if hasattr(report_date, 'date') else report_date,
                file_path,
                update_count,
                json.dumps(metadata, default=str) if metadata else None
            ))
    
    def check_rate_limit(self, service: str, max_calls: int, 
                        period_seconds: int) -> bool:
        """Check if we can make an API call within rate limits"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            reset_time = datetime.now() - timedelta(seconds=period_seconds)
            
            # Clean old entries
            cursor.execute("""
                DELETE FROM rate_limits 
                WHERE service = ? AND last_call < ?
            """, (service, reset_time.isoformat()))
            
            # Count recent calls
            cursor.execute("""
                SELECT COUNT(*) as count FROM rate_limits 
                WHERE service = ? AND last_call >= ?
            """, (service, reset_time.isoformat()))
            
            result = cursor.fetchone()
            current_calls = result['count'] if result else 0
            
            if current_calls < max_calls:
                # Record this call
                cursor.execute("""
                    INSERT INTO rate_limits (service, last_call)
                    VALUES (?, CURRENT_TIMESTAMP)
                """, (service,))
                return True
            
            return False
    
    def calculate_importance_scores(self) -> None:
        """Calculate importance scores for updates based on various factors"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Simple scoring based on keywords and recency
            cursor.execute("""
                UPDATE updates
                SET importance_score = 
                    CASE 
                        WHEN LOWER(title) LIKE '%claude%' THEN 10
                        WHEN LOWER(title) LIKE '%anthropic%' THEN 9
                        WHEN LOWER(title) LIKE '%gpt%' OR LOWER(title) LIKE '%openai%' THEN 8
                        WHEN LOWER(title) LIKE '%gemini%' OR LOWER(title) LIKE '%google%' THEN 7
                        WHEN LOWER(title) LIKE '%mcp%' OR LOWER(title) LIKE '%model context%' THEN 6
                        WHEN LOWER(title) LIKE '%agent%' THEN 5
                        ELSE 3
                    END +
                    CASE 
                        WHEN julianday('now') - julianday(published_date) < 1 THEN 5
                        WHEN julianday('now') - julianday(published_date) < 3 THEN 3
                        WHEN julianday('now') - julianday(published_date) < 7 THEN 1
                        ELSE 0
                    END
                WHERE importance_score = 0
            """)