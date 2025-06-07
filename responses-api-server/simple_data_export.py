#!/usr/bin/env python3
"""
Simple CS 15 Tutor Database Data Export

A straightforward script to extract and view data from the database.
"""

from database import db_manager, AnonymousUser, Conversation, Message, UserSession
from datetime import datetime, timedelta
import json

def show_all_data():
    """Show all data in the database"""
    print("="*60)
    print(" CS 15 TUTOR DATABASE CONTENTS")
    print("="*60)
    
    db = db_manager.get_session()
    try:
        # Get all users
        users = db.query(AnonymousUser).all()
        print(f"\n👥 ANONYMOUS USERS ({len(users)} total):")
        for user in users:
            print(f"  ID: {user.anonymous_id}")
            print(f"  Created: {user.created_at}")
            print(f"  Last Active: {user.last_active}")
            print()
        
        # Get all conversations
        conversations = db.query(Conversation).all()
        print(f"💬 CONVERSATIONS ({len(conversations)} total):")
        for convo in conversations:
            print(f"  User: {convo.user.anonymous_id}")
            print(f"  Platform: {convo.platform}")
            print(f"  Created: {convo.created_at}")
            print(f"  Messages: {convo.message_count}")
            print(f"  ID: {convo.conversation_id}")
            print()
        
        # Get all messages
        messages = db.query(Message).all()
        print(f"📝 MESSAGES ({len(messages)} total):")
        for msg in messages:
            print(f"  Type: {msg.message_type}")
            print(f"  Time: {msg.created_at}")
            print(f"  Content: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
            if msg.model_used:
                print(f"  Model: {msg.model_used}")
            if msg.response_time_ms:
                print(f"  Response Time: {msg.response_time_ms}ms")
            print()
            
    finally:
        db.close()

def export_to_json(filename="cs15_data_export.json"):
    """Export all data to JSON format"""
    print(f"📄 Exporting data to {filename}...")
    
    db = db_manager.get_session()
    try:
        data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "users": [],
            "conversations": [],
            "messages": []
        }
        
        # Export users
        users = db.query(AnonymousUser).all()
        for user in users:
            data["users"].append({
                "anonymous_id": user.anonymous_id,
                "created_at": user.created_at.isoformat(),
                "last_active": user.last_active.isoformat()
            })
        
        # Export conversations
        conversations = db.query(Conversation).all()
        for convo in conversations:
            data["conversations"].append({
                "conversation_id": convo.conversation_id,
                "user_anonymous_id": convo.user.anonymous_id,
                "platform": convo.platform,
                "created_at": convo.created_at.isoformat(),
                "last_message_at": convo.last_message_at.isoformat(),
                "message_count": convo.message_count
            })
        
        # Export messages (be careful with content - you may want to limit this)
        messages = db.query(Message).all()
        for msg in messages:
            data["messages"].append({
                "conversation_id": msg.conversation.conversation_id,
                "message_type": msg.message_type,
                "content_length": len(msg.content),  # Length instead of full content for privacy
                "content_preview": msg.content[:200],  # Just a preview
                "model_used": msg.model_used,
                "response_time_ms": msg.response_time_ms,
                "created_at": msg.created_at.isoformat()
            })
        
        # Write to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(users)} users, {len(conversations)} conversations, {len(messages)} messages")
        
    finally:
        db.close()

def search_by_user(anonymous_id):
    """Find all data for a specific anonymous user"""
    print(f"🔍 Searching for user: {anonymous_id}")
    
    db = db_manager.get_session()
    try:
        user = db.query(AnonymousUser).filter(AnonymousUser.anonymous_id == anonymous_id).first()
        if not user:
            print(f"❌ User {anonymous_id} not found")
            return
        
        print(f"👤 User Details:")
        print(f"  Anonymous ID: {user.anonymous_id}")
        print(f"  Created: {user.created_at}")
        print(f"  Last Active: {user.last_active}")
        
        conversations = db.query(Conversation).filter(Conversation.user_id == user.id).all()
        print(f"\n💬 Conversations ({len(conversations)}):")
        
        for convo in conversations:
            print(f"  📱 {convo.platform} conversation")
            print(f"    Started: {convo.created_at}")
            print(f"    Messages: {convo.message_count}")
            
            messages = db.query(Message).filter(Message.conversation_id == convo.id).all()
            for msg in messages:
                print(f"    {msg.message_type}: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
            print()
            
    finally:
        db.close()

def show_recent_activity(hours=24):
    """Show activity from the last N hours"""
    print(f"📈 Recent Activity (last {hours} hours)")
    
    db = db_manager.get_session()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        recent_messages = db.query(Message).filter(Message.created_at >= cutoff).all()
        print(f"📝 {len(recent_messages)} recent messages:")
        
        for msg in recent_messages:
            convo = msg.conversation
            print(f"  {msg.created_at.strftime('%Y-%m-%d %H:%M')} - {convo.user.anonymous_id} ({convo.platform})")
            print(f"    {msg.message_type}: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
            print()
            
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Simple CS 15 Tutor Data Export")
        print("\nCommands:")
        print("  python simple_data_export.py show        - Show all data")
        print("  python simple_data_export.py export      - Export to JSON")
        print("  python simple_data_export.py user <id>   - Search by user ID")
        print("  python simple_data_export.py recent [hours] - Recent activity")
        print("\nExamples:")
        print("  python simple_data_export.py show")
        print("  python simple_data_export.py user aaaaaa00")
        print("  python simple_data_export.py recent 6")
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "show":
        show_all_data()
    elif command == "export":
        export_to_json()
    elif command == "user":
        if len(sys.argv) < 3:
            print("❌ Please provide a user ID")
        else:
            search_by_user(sys.argv[2])
    elif command == "recent":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        show_recent_activity(hours)
    else:
        print(f"❌ Unknown command: {command}") 