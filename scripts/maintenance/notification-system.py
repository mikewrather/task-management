#!/usr/bin/env python3
"""
Notification system for voice processing
Supports desktop notifications, email alerts, and status reports
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Email imports - handle gracefully if not available
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

project_root = Path(__file__).parent.parent

def send_desktop_notification(title, message, urgency="normal"):
    """Send desktop notification using notify-send"""
    try:
        subprocess.run([
            'notify-send', 
            '--urgency', urgency,
            '--icon', 'audio-headphones',
            '--app-name', 'Voice Processor',
            title, 
            message
        ], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: try with simpler notify-send
        try:
            subprocess.run(['notify-send', title, message], check=True)
            return True
        except:
            return False

def send_email_notification(subject, body, to_email=None):
    """Send email notification (configure SMTP settings in .env)"""
    if not EMAIL_AVAILABLE:
        return False
    
    try:
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASS')
        from_email = os.getenv('FROM_EMAIL', smtp_user)
        to_email = to_email or os.getenv('NOTIFICATION_EMAIL')
        
        if not all([smtp_server, smtp_user, smtp_pass, to_email]):
            return False
        
        msg = MimeMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MimeText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False

def get_processing_stats():
    """Get processing statistics from database"""
    db_path = project_root / 'data' / 'processed_files.db'
    if not db_path.exists():
        return {'total': 0, 'today': 0, 'recent': []}
    
    conn = sqlite3.connect(db_path)
    
    # Total processed
    total = conn.execute('SELECT COUNT(*) FROM processed_files').fetchone()[0]
    
    # Today's count
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = conn.execute(
        'SELECT COUNT(*) FROM processed_files WHERE DATE(processed_at) = ?', 
        (today,)
    ).fetchone()[0]
    
    # Recent files (last 24 hours)
    yesterday = datetime.now() - timedelta(hours=24)
    recent = conn.execute(
        '''SELECT file_id, processed_at, transcript, task_url 
           FROM processed_files 
           WHERE processed_at > ? 
           ORDER BY processed_at DESC''', 
        (yesterday,)
    ).fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'today': today_count,
        'recent': recent
    }

def notify_processing_success(file_id, transcript, task_url):
    """Send notifications when a file is successfully processed"""
    
    # Truncate transcript for notification
    short_transcript = transcript[:100] + "..." if len(transcript) > 100 else transcript
    
    # Desktop notification
    title = "🎤 Voice Note Processed"
    message = f"Created task: {short_transcript}"
    
    desktop_sent = send_desktop_notification(title, message)
    
    # Email notification (if configured)
    email_subject = "Voice Note Processed Successfully"
    email_body = f"""
Your voice note has been processed and added to Notion:

Transcript: {transcript}

Task URL: {task_url}

File ID: {file_id}
Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
Voice Task Management System
"""
    
    email_sent = send_email_notification(email_subject, email_body)
    
    # Log notification results
    log_msg = f"📢 Notifications sent for {file_id}: Desktop={desktop_sent}, Email={email_sent}"
    print(log_msg)
    
    # Also log to file
    log_file = project_root / 'logs' / 'voice-automation.log'
    with open(log_file, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] {log_msg}\n")

def generate_daily_summary():
    """Generate daily processing summary"""
    stats = get_processing_stats()
    
    if stats['today'] == 0:
        return "📭 No voice notes processed today"
    
    summary = f"""
📊 Daily Voice Processing Summary

Today: {stats['today']} files processed
Total: {stats['total']} files processed

Recent Activity:
"""
    
    for file_id, processed_at, transcript, task_url in stats['recent'][-5:]:
        timestamp = datetime.fromisoformat(processed_at).strftime('%H:%M')
        short_transcript = transcript[:50] + "..." if len(transcript) > 50 else transcript
        summary += f"  • {timestamp}: {short_transcript}\n"
    
    summary += f"\n📋 View all tasks: https://www.notion.so/183267fb-e1c1-4b3b-a42a-5ac1ab8353eb"
    
    return summary

def main():
    """Main notification function - can be called from automation script"""
    if len(sys.argv) < 2:
        print("Usage: python notification-system.py <command> [args...]")
        print("Commands:")
        print("  success <file_id> <transcript> <task_url>  - Notify processing success")
        print("  summary                                     - Show daily summary")
        print("  test                                        - Test notifications")
        return
    
    command = sys.argv[1]
    
    if command == 'success' and len(sys.argv) >= 5:
        file_id = sys.argv[2]
        transcript = sys.argv[3]
        task_url = sys.argv[4]
        notify_processing_success(file_id, transcript, task_url)
        
    elif command == 'summary':
        summary = generate_daily_summary()
        print(summary)
        
    elif command == 'test':
        print("🧪 Testing notification system...")
        
        # Test desktop notification
        desktop_ok = send_desktop_notification(
            "🧪 Test Notification", 
            "Voice processing system is working!"
        )
        print(f"Desktop notification: {'✅' if desktop_ok else '❌'}")
        
        # Test email (if configured)
        email_ok = send_email_notification(
            "Test Voice Processing Notification",
            "This is a test email from your voice processing system."
        )
        print(f"Email notification: {'✅' if email_ok else '❌ (not configured)'}")
        
        # Show stats
        stats = get_processing_stats()
        print(f"Database stats: {stats['total']} total, {stats['today']} today")
        
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()