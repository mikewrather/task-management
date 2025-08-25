#!/usr/bin/env python3
"""
Reset the last N voice files to unprocessed status
"""

import sqlite3
from pathlib import Path
import sys

def reset_last_files(n=5):
    """Mark the last N voice files as unprocessed"""
    
    db_path = Path(__file__).parent / "data" / "processed_files.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the last N processed files
        cursor.execute("""
            SELECT file_id, transcript 
            FROM processed_files 
            WHERE status = 'completed'
            ORDER BY processed_at DESC 
            LIMIT ?
        """, (n,))
        
        files = cursor.fetchall()
        
        if not files:
            print("❌ No completed files found to reset")
            return False
        
        print(f"Found {len(files)} files to reset:")
        for file_id, transcription in files:
            preview = (transcription[:50] + "...") if transcription and len(transcription) > 50 else transcription
            print(f"  - {file_id}: {preview}")
        
        # Reset their status
        file_ids = [f[0] for f in files]
        placeholders = ','.join(['?' for _ in file_ids])
        
        cursor.execute(f"""
            UPDATE processed_files 
            SET status = 'pending',
                processed_at = NULL,
                task_url = NULL,
                error_message = NULL
            WHERE file_id IN ({placeholders})
        """, file_ids)
        
        conn.commit()
        print(f"\n✅ Reset {len(files)} files to pending status")
        
        # Show current status
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM processed_files 
            GROUP BY status
        """)
        
        print("\n📊 Current file status:")
        for status, count in cursor.fetchall():
            print(f"  - {status}: {count} files")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error resetting files: {e}")
        return False

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(f"🔄 Resetting last {n} voice files to unprocessed status...")
    print("=" * 50)
    
    if reset_last_files(n):
        print("\n✅ Files reset successfully!")
        print("You can now run 'vtm process' to reprocess them")
    else:
        print("\n❌ Failed to reset files")