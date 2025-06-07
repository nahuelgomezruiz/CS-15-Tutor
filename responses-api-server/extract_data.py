#!/usr/bin/env python3
"""
CS 15 Tutor Database Data Extraction Tool

This script provides various ways to extract and analyze data from the CS 15 Tutor database.
All user data is anonymized - no real UTLNs are stored or displayed.
"""

import sys
import os
from datetime import datetime, timedelta
import json
import csv
from database import db_manager, AnonymousUser, Conversation, Message, UserSession

def print_separator(title=""):
    """Print a nice separator"""
    print("\n" + "="*60)
    if title:
        print(f" {title} ")
        print("="*60)

def get_system_overview():
    """Get high-level system statistics"""
    print_separator("SYSTEM OVERVIEW")
    
    db = db_manager.get_session()
    try:
        # Basic counts
        total_users = db.query(AnonymousUser).count()
        total_conversations = db.query(Conversation).count()
        total_messages = db.query(Message).count()
        
        # Platform breakdown
        web_convos = db.query(Conversation).filter(Conversation.platform == 'web').count()
        vscode_convos = db.query(Conversation).filter(Conversation.platform == 'vscode').count()
        
        # Message types
        queries = db.query(Message).filter(Message.message_type == 'query').count()
        responses = db.query(Message).filter(Message.message_type == 'response').count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_users = db.query(AnonymousUser).filter(AnonymousUser.last_active >= week_ago).count()
        recent_messages = db.query(Message).filter(Message.created_at >= week_ago).count()
        
        print(f"📊 Total Anonymous Users: {total_users}")
        print(f"💬 Total Conversations: {total_conversations}")
        print(f"📝 Total Messages: {total_messages}")
        print(f"   ├─ Queries: {queries}")
        print(f"   └─ Responses: {responses}")
        print()
        print(f"🌐 Platform Usage:")
        print(f"   ├─ Web App: {web_convos} conversations")
        print(f"   └─ VSCode: {vscode_convos} conversations")
        print()
        print(f"📈 Recent Activity (7 days):")
        print(f"   ├─ Active Users: {recent_users}")
        print(f"   └─ Messages: {recent_messages}")
        
        if total_users > 0:
            avg_convos = total_conversations / total_users
            print(f"\n📋 Averages:")
            print(f"   ├─ Conversations per user: {avg_convos:.2f}")
            if total_conversations > 0:
                avg_msgs = total_messages / total_conversations
                print(f"   └─ Messages per conversation: {avg_msgs:.2f}")
                
    finally:
        db.close()

def get_user_activity():
    """Show user activity patterns"""
    print_separator("USER ACTIVITY PATTERNS")
    
    db = db_manager.get_session()
    try:
        # Most active users
        print("🏆 Top 10 Most Active Users:")
        users_with_message_counts = db.query(
            AnonymousUser.anonymous_id,
            AnonymousUser.created_at,
            AnonymousUser.last_active,
            db.func.count(Message.id).label('message_count')
        ).join(Conversation).join(Message).group_by(AnonymousUser.id).order_by(
            db.func.count(Message.id).desc()
        ).limit(10).all()
        
        for i, (anon_id, created, last_active, msg_count) in enumerate(users_with_message_counts, 1):
            days_active = (last_active - created).days
            print(f"{i:2}. {anon_id} - {msg_count} messages, {days_active} days active")
        
        # Platform preferences
        print("\n📱 Platform Preferences:")
        platform_users = db.query(
            Conversation.platform,
            db.func.count(db.func.distinct(AnonymousUser.id)).label('unique_users')
        ).join(AnonymousUser).group_by(Conversation.platform).all()
        
        for platform, user_count in platform_users:
            print(f"   {platform}: {user_count} unique users")
            
    finally:
        db.close()

def get_recent_conversations(days=7):
    """Show recent conversation details"""
    print_separator(f"RECENT CONVERSATIONS (Last {days} days)")
    
    db = db_manager.get_session()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_convos = db.query(Conversation).filter(
            Conversation.created_at >= cutoff
        ).order_by(Conversation.created_at.desc()).limit(20).all()
        
        print(f"📅 Showing {len(recent_convos)} most recent conversations:")
        print()
        
        for convo in recent_convos:
            # Get message count for this conversation
            msg_count = db.query(Message).filter(Message.conversation_id == convo.id).count()
            
            duration = convo.last_message_at - convo.created_at
            duration_mins = int(duration.total_seconds() / 60)
            
            print(f"🗨️  {convo.user.anonymous_id} on {convo.platform}")
            print(f"   ├─ Started: {convo.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   ├─ Duration: {duration_mins} minutes")
            print(f"   ├─ Messages: {msg_count}")
            print(f"   └─ ID: {convo.conversation_id[:8]}...")
            print()
            
    finally:
        db.close()

def export_messages_to_csv(filename="messages_export.csv", days=30):
    """Export recent messages to CSV for analysis"""
    print_separator(f"EXPORTING MESSAGES TO {filename}")
    
    db = db_manager.get_session()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get messages with user and conversation info
        messages = db.query(
            Message.created_at,
            Message.message_type,
            Message.content,
            Message.model_used,
            Message.response_time_ms,
            AnonymousUser.anonymous_id,
            Conversation.platform,
            Conversation.conversation_id
        ).join(Conversation).join(AnonymousUser).filter(
            Message.created_at >= cutoff
        ).order_by(Message.created_at.desc()).all()
        
        # Write to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'timestamp', 'message_type', 'anonymous_user', 'platform', 
                'conversation_id', 'model_used', 'response_time_ms', 'content_length'
            ])
            
            for msg in messages:
                writer.writerow([
                    msg.created_at.isoformat(),
                    msg.message_type,
                    msg.anonymous_id,
                    msg.platform,
                    msg.conversation_id[:8] + "...",  # Truncate for privacy
                    msg.model_used or 'N/A',
                    msg.response_time_ms or 0,
                    len(msg.content)  # Content length instead of actual content
                ])
        
        print(f"✅ Exported {len(messages)} messages to {filename}")
        print(f"📊 Data includes last {days} days of activity")
        
    finally:
        db.close()

def search_conversations(user_id=None, platform=None, days=None):
    """Search for specific conversations"""
    print_separator("CONVERSATION SEARCH")
    
    db = db_manager.get_session()
    try:
        query = db.query(Conversation).join(AnonymousUser)
        
        if user_id:
            query = query.filter(AnonymousUser.anonymous_id == user_id)
            print(f"🔍 Filtering by user: {user_id}")
        
        if platform:
            query = query.filter(Conversation.platform == platform)
            print(f"🔍 Filtering by platform: {platform}")
        
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Conversation.created_at >= cutoff)
            print(f"🔍 Filtering by recency: last {days} days")
        
        conversations = query.order_by(Conversation.created_at.desc()).limit(50).all()
        
        print(f"\n📋 Found {len(conversations)} conversations:")
        
        for convo in conversations:
            msg_count = db.query(Message).filter(Message.conversation_id == convo.id).count()
            print(f"  {convo.user.anonymous_id} | {convo.platform} | {msg_count} msgs | {convo.created_at.strftime('%Y-%m-%d %H:%M')}")
            
    finally:
        db.close()

def get_analytics_summary():
    """Get comprehensive analytics for reporting"""
    print_separator("ANALYTICS SUMMARY")
    
    db = db_manager.get_session()
    try:
        # Time-based analytics
        now = datetime.utcnow()
        periods = [
            ("Today", now - timedelta(days=1)),
            ("This Week", now - timedelta(days=7)),
            ("This Month", now - timedelta(days=30))
        ]
        
        for period_name, cutoff in periods:
            users = db.query(AnonymousUser).filter(AnonymousUser.last_active >= cutoff).count()
            messages = db.query(Message).filter(Message.created_at >= cutoff).count()
            convos = db.query(Conversation).filter(Conversation.created_at >= cutoff).count()
            
            print(f"📈 {period_name}:")
            print(f"   ├─ Active Users: {users}")
            print(f"   ├─ New Conversations: {convos}")
            print(f"   └─ Messages: {messages}")
            print()
        
        # Response time analytics
        avg_response_time = db.query(db.func.avg(Message.response_time_ms)).filter(
            Message.response_time_ms.isnot(None)
        ).scalar()
        
        if avg_response_time:
            print(f"⚡ Average Response Time: {avg_response_time:.0f}ms")
        
    finally:
        db.close()

def main():
    """Main function - run different analysis based on command line args"""
    if len(sys.argv) < 2:
        print("CS 15 Tutor Database Extraction Tool")
        print("\nUsage:")
        print("  python extract_data.py overview       - System overview")
        print("  python extract_data.py users          - User activity patterns")
        print("  python extract_data.py recent [days]  - Recent conversations")
        print("  python extract_data.py export [days]  - Export to CSV")
        print("  python extract_data.py search [user] [platform] [days]")
        print("  python extract_data.py analytics      - Full analytics report")
        print("\nExamples:")
        print("  python extract_data.py overview")
        print("  python extract_data.py recent 3")
        print("  python extract_data.py export 14")
        print("  python extract_data.py search aaaaaa00")
        print("  python extract_data.py search '' web 7")
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "overview":
            get_system_overview()
        
        elif command == "users":
            get_user_activity()
        
        elif command == "recent":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            get_recent_conversations(days)
        
        elif command == "export":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            export_messages_to_csv(f"cs15_messages_{days}days.csv", days)
        
        elif command == "search":
            user_id = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
            platform = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
            days = int(sys.argv[4]) if len(sys.argv) > 4 else None
            search_conversations(user_id, platform, days)
        
        elif command == "analytics":
            get_analytics_summary()
            get_system_overview()
            get_user_activity()
        
        else:
            print(f"❌ Unknown command: {command}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the database exists and is accessible.")

if __name__ == "__main__":
    main() 