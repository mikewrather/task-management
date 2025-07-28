"""
Database Operations for Voice Task Manager
Enhanced SQLite operations with modern Python practices and deprecation fixes.
"""

import sqlite3
import warnings
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from contextlib import contextmanager

# Suppress SQLite deprecation warnings for Python 3.12+
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlite3")

from ..models.voice_file import VoiceFile
from ..models.task import NotionTask

class VoiceDatabase:
    """Enhanced database operations for voice processing system"""
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """
        Initialize database connection
        
        Args:
            project_root: Root directory of the project (auto-detected if None)
        """
        if project_root is None:
            # Auto-detect project root from package location
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # Ensure data directory exists
        self.data_dir = self.project_root / 'data'
        self.data_dir.mkdir(exist_ok=True)
        
        self.db_path = self.data_dir / 'processed_files.db'
        
        # Initialize logger for migration messages
        from .logging import VoiceLogger
        self.logger = VoiceLogger(self.project_root)
        
        # Initialize database schema
        self._init_schema()
    
    def _init_schema(self) -> None:
        """Initialize database schema with enhanced tables and migration support"""
        with self.get_connection() as conn:
            # Create the basic processed_files table (backward compatible)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_files (
                    file_id TEXT PRIMARY KEY,
                    processed_at TIMESTAMP,
                    transcript TEXT,
                    task_url TEXT
                )
            ''')
            
            # Add new columns if they don't exist (migration support)
            self._add_column_if_not_exists(conn, 'processed_files', 'discovered_at', 'TIMESTAMP')
            self._add_column_if_not_exists(conn, 'processed_files', 'status', 'TEXT DEFAULT "completed"')
            self._add_column_if_not_exists(conn, 'processed_files', 'file_size', 'INTEGER')
            self._add_column_if_not_exists(conn, 'processed_files', 'content_type', 'TEXT')
            self._add_column_if_not_exists(conn, 'processed_files', 'transcript_length', 'INTEGER')
            self._add_column_if_not_exists(conn, 'processed_files', 'duration_seconds', 'REAL')
            self._add_column_if_not_exists(conn, 'processed_files', 'error_message', 'TEXT')
            self._add_column_if_not_exists(conn, 'processed_files', 'retry_count', 'INTEGER DEFAULT 0')
            self._add_column_if_not_exists(conn, 'processed_files', 'metadata', 'TEXT')
            self._add_column_if_not_exists(conn, 'processed_files', 'archive_status', 'TEXT DEFAULT "active"')
            self._add_column_if_not_exists(conn, 'processed_files', 'archived_at', 'TIMESTAMP')
            
            # New tasks table for better task tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT,
                    status TEXT DEFAULT 'Inbox',
                    contexts TEXT,  -- JSON array
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP,
                    url TEXT,
                    voice_file_id TEXT,
                    transcript_source TEXT,
                    metadata TEXT,  -- JSON string
                    FOREIGN KEY (voice_file_id) REFERENCES processed_files (file_id)
                )
            ''')
            
            # Create indexes for better performance (only if columns exist)
            self._create_index_if_column_exists(conn, 'idx_files_status', 'processed_files', 'status')
            self._create_index_if_column_exists(conn, 'idx_files_processed_at', 'processed_files', 'processed_at')
            self._create_index_if_column_exists(conn, 'idx_tasks_status', 'tasks', 'status')
            self._create_index_if_column_exists(conn, 'idx_tasks_created_at', 'tasks', 'created_at')
            self._create_index_if_column_exists(conn, 'idx_tasks_voice_file', 'tasks', 'voice_file_id')
            
            conn.commit()
    
    def _add_column_if_not_exists(self, conn, table_name: str, column_name: str, column_def: str) -> None:
        """Add a column to a table if it doesn't already exist"""
        try:
            # Check if column exists by trying to select it
            conn.execute(f'SELECT {column_name} FROM {table_name} LIMIT 1')
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            try:
                conn.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}')
                self.logger.info(f"Added column {column_name} to table {table_name}")
            except sqlite3.OperationalError as e:
                self.logger.warning(f"Failed to add column {column_name}: {e}")
    
    def _create_index_if_column_exists(self, conn, index_name: str, table_name: str, column_name: str) -> None:
        """Create an index only if the column exists"""
        try:
            # Check if column exists
            conn.execute(f'SELECT {column_name} FROM {table_name} LIMIT 1')
            # Column exists, create index
            conn.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})')
        except sqlite3.OperationalError:
            # Column doesn't exist, skip index creation
            pass
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    # Voice File Operations
    
    def save_voice_file(self, voice_file: VoiceFile) -> None:
        """Save or update a voice file record"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO processed_files (
                    file_id, discovered_at, processed_at, status, file_size, content_type,
                    transcript, transcript_length, duration_seconds, task_url,
                    error_message, retry_count, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                voice_file.file_id,
                voice_file.discovered_at,
                voice_file.processed_at,
                voice_file.status,
                voice_file.file_size,
                voice_file.content_type,
                voice_file.transcript,
                voice_file.transcript_length,
                voice_file.duration_seconds,
                voice_file.task_url,
                voice_file.error_message,
                voice_file.retry_count,
                str(voice_file.metadata) if voice_file.metadata else None
            ))
            conn.commit()
    
    def get_voice_file(self, file_id: str) -> Optional[VoiceFile]:
        """Get a voice file by ID"""
        with self.get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM processed_files WHERE file_id = ?', 
                (file_id,)
            ).fetchone()
            
            if row:
                return self._row_to_voice_file(row)
            return None
    
    def is_file_processed(self, file_id: str) -> bool:
        """Check if file has been processed (backward compatible)"""
        with self.get_connection() as conn:
            row = conn.execute(
                'SELECT file_id FROM processed_files WHERE file_id = ? AND status = ?',
                (file_id, 'completed')
            ).fetchone()
            return row is not None
    
    def get_all_voice_files(self, status: Optional[str] = None, 
                           limit: Optional[int] = None) -> List[VoiceFile]:
        """Get all voice files, optionally filtered by status"""
        with self.get_connection() as conn:
            query = 'SELECT * FROM processed_files'
            params = []
            
            if status:
                query += ' WHERE status = ?'
                params.append(status)
            
            query += ' ORDER BY discovered_at DESC'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_voice_file(row) for row in rows]
    
    def get_files_by_date_range(self, start_date: datetime, 
                               end_date: datetime) -> List[VoiceFile]:
        """Get voice files within a date range"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM processed_files 
                WHERE discovered_at BETWEEN ? AND ?
                ORDER BY discovered_at DESC
            ''', (start_date, end_date)).fetchall()
            
            return [self._row_to_voice_file(row) for row in rows]
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        with self.get_connection() as conn:
            # Basic counts
            total_files = conn.execute('SELECT COUNT(*) FROM processed_files').fetchone()[0]
            completed_files = conn.execute(
                'SELECT COUNT(*) FROM processed_files WHERE status = ?', 
                ('completed',)
            ).fetchone()[0]
            failed_files = conn.execute(
                'SELECT COUNT(*) FROM processed_files WHERE status = ?',
                ('failed',)
            ).fetchone()[0]
            
            # Today's activity
            today = datetime.now().strftime('%Y-%m-%d')
            today_processed = conn.execute(
                'SELECT COUNT(*) FROM processed_files WHERE DATE(processed_at) = ?',
                (today,)
            ).fetchone()[0]
            
            # Average processing time
            avg_processing_time = conn.execute('''
                SELECT AVG(
                    (julianday(processed_at) - julianday(discovered_at)) * 86400
                ) FROM processed_files 
                WHERE processed_at IS NOT NULL AND discovered_at IS NOT NULL
            ''').fetchone()[0]
            
            # Success rate
            success_rate = (completed_files / max(total_files, 1)) * 100
            
            return {
                'total_files': total_files,
                'completed_files': completed_files,
                'failed_files': failed_files,
                'pending_files': total_files - completed_files - failed_files,
                'today_processed': today_processed,
                'success_rate': round(success_rate, 1),
                'avg_processing_time_seconds': round(avg_processing_time or 0, 2)
            }
    
    # Task Operations
    
    def save_task(self, task: NotionTask) -> None:
        """Save or update a task record"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO tasks (
                    task_id, title, content, status, contexts, created_at, updated_at,
                    url, voice_file_id, transcript_source, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.task_id,
                task.title,
                task.content,
                task.status,
                str(task.contexts),  # Store as JSON string
                task.created_at,
                task.updated_at,
                task.url,
                task.voice_file_id,
                task.transcript_source,
                str(task.metadata) if task.metadata else None
            ))
            conn.commit()
    
    def get_task(self, task_id: str) -> Optional[NotionTask]:
        """Get a task by ID"""
        with self.get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM tasks WHERE task_id = ?',
                (task_id,)
            ).fetchone()
            
            if row:
                return self._row_to_task(row)
            return None
    
    def get_tasks_by_voice_file(self, file_id: str) -> List[NotionTask]:
        """Get all tasks created from a specific voice file"""
        with self.get_connection() as conn:
            rows = conn.execute(
                'SELECT * FROM tasks WHERE voice_file_id = ? ORDER BY created_at DESC',
                (file_id,)
            ).fetchall()
            
            return [self._row_to_task(row) for row in rows]
    
    # Legacy compatibility methods
    
    def mark_as_processed(self, file_id: str, transcript: str, task_url: str) -> None:
        """Legacy method for backward compatibility"""
        voice_file = self.get_voice_file(file_id)
        if not voice_file:
            # Create new record with minimal data
            voice_file = VoiceFile(file_id=file_id)
        
        voice_file.mark_completed(transcript, task_url)
        self.save_voice_file(voice_file)
    
    # Utility methods
    
    def _row_to_voice_file(self, row) -> VoiceFile:
        """Convert database row to VoiceFile object"""
        # Handle backward compatibility with old schema
        # Convert row to dict to handle both sqlite3.Row and dict objects
        if hasattr(row, 'keys'):
            row_dict = dict(row)
        else:
            row_dict = row
        
        return VoiceFile(
            file_id=row_dict['file_id'],
            discovered_at=datetime.fromisoformat(row_dict['discovered_at']) if row_dict.get('discovered_at') else datetime.now(),
            processed_at=datetime.fromisoformat(row_dict['processed_at']) if row_dict.get('processed_at') else None,
            status=row_dict.get('status', 'completed'),
            file_size=row_dict.get('file_size'),
            content_type=row_dict.get('content_type'),
            transcript=row_dict.get('transcript'),
            transcript_length=row_dict.get('transcript_length'),
            duration_seconds=row_dict.get('duration_seconds'),
            task_url=row_dict.get('task_url'),
            error_message=row_dict.get('error_message'),
            retry_count=row_dict.get('retry_count', 0),
            metadata=eval(row_dict['metadata']) if row_dict.get('metadata') else {},
            archive_status=row_dict.get('archive_status', 'active'),
            archived_at=datetime.fromisoformat(row_dict['archived_at']) if row_dict.get('archived_at') else None
        )
    
    def _row_to_task(self, row) -> NotionTask:
        """Convert database row to NotionTask object"""
        # Convert row to dict to handle both sqlite3.Row and dict objects
        if hasattr(row, 'keys'):
            row_dict = dict(row)
        else:
            row_dict = row
            
        return NotionTask(
            task_id=row_dict['task_id'],
            title=row_dict['title'],
            content=row_dict.get('content', ''),
            status=row_dict.get('status', 'Inbox'),
            contexts=eval(row_dict['contexts']) if row_dict.get('contexts') else ['voice'],
            created_at=datetime.fromisoformat(row_dict['created_at']),
            updated_at=datetime.fromisoformat(row_dict['updated_at']) if row_dict.get('updated_at') else None,
            url=row_dict.get('url'),
            voice_file_id=row_dict.get('voice_file_id'),
            transcript_source=row_dict.get('transcript_source'),
            metadata=eval(row_dict['metadata']) if row_dict.get('metadata') else {}
        )
    
    def cleanup_old_records(self, days_old: int = 90) -> int:
        """Clean up old processed file records"""
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM processed_files 
                WHERE discovered_at < ? AND status = 'completed'
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count
    
    def vacuum_database(self) -> None:
        """Optimize database by running VACUUM"""
        with self.get_connection() as conn:
            conn.execute('VACUUM')
    
    def mark_file_for_archive(self, file_id: str) -> bool:
        """
        Mark a processed file for archival
        
        Args:
            file_id: Google Drive file ID to mark for archive
            
        Returns:
            True if successfully marked, False if file not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE processed_files 
                SET archive_status = 'pending_archive', archived_at = ?
                WHERE file_id = ? AND status = 'completed'
            ''', (datetime.now(), file_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def mark_file_archived(self, file_id: str) -> bool:
        """
        Mark a file as successfully archived
        
        Args:
            file_id: Google Drive file ID that was archived
            
        Returns:
            True if successfully marked, False if file not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE processed_files 
                SET archive_status = 'archived', archived_at = ?
                WHERE file_id = ?
            ''', (datetime.now(), file_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_files_pending_archive(self) -> List[VoiceFile]:
        """Get files that are marked for archival but not yet archived"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM processed_files 
                WHERE archive_status = 'pending_archive'
                ORDER BY processed_at ASC
            ''').fetchall()
            
            return [self._row_to_voice_file(row) for row in rows]
    
    def get_archived_files(self, limit: Optional[int] = None) -> List[VoiceFile]:
        """
        Get files that have been archived
        
        Args:
            limit: Maximum number of files to return
            
        Returns:
            List of archived VoiceFile objects
        """
        with self.get_connection() as conn:
            query = '''
                SELECT * FROM processed_files 
                WHERE archive_status = 'archived'
                ORDER BY archived_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            rows = conn.execute(query).fetchall()
            return [self._row_to_voice_file(row) for row in rows]
    
    def get_archive_statistics(self) -> Dict[str, Any]:
        """Get statistics about archived files"""
        with self.get_connection() as conn:
            active_count = conn.execute(
                'SELECT COUNT(*) FROM processed_files WHERE archive_status = "active"'
            ).fetchone()[0]
            
            pending_archive_count = conn.execute(
                'SELECT COUNT(*) FROM processed_files WHERE archive_status = "pending_archive"'
            ).fetchone()[0]
            
            archived_count = conn.execute(
                'SELECT COUNT(*) FROM processed_files WHERE archive_status = "archived"'
            ).fetchone()[0]
            
            # Recent archival activity
            recent_archived = conn.execute('''
                SELECT COUNT(*) FROM processed_files 
                WHERE archive_status = "archived" 
                AND archived_at > datetime('now', '-7 days')
            ''').fetchone()[0]
            
            return {
                'active_files': active_count,
                'pending_archive': pending_archive_count,
                'archived_count': archived_count,
                'recent_archived': recent_archived,
                'total_files': active_count + pending_archive_count + archived_count
            }

# Convenience function for easy access
def get_database(project_root: Optional[Union[str, Path]] = None) -> VoiceDatabase:
    """Get a VoiceDatabase instance"""
    return VoiceDatabase(project_root)