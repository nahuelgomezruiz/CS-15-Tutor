#!/usr/bin/env python3
"""
Export SQLite Data for CS 15 Tutor Database

This script exports all data from the current SQLite database to JSON format
for backup purposes and potential migration to PostgreSQL.
"""

import os
import json
import sqlite3
from datetime import datetime
from database import db_manager, AnonymousUser, Conversation, Message, UserHealthPoints

def export_sqlite_to_json():
    """Export all SQLite data to JSON files"""
    
    # Check if SQLite database exists
    if not os.path.exists('cs15_tutor_logs.db'):
        print("❌ No SQLite database found (cs15_tutor_logs.db)")
        return False
    
    print("📊 Exporting SQLite database...")
    
    try:
        # Connect directly to SQLite
        conn = sqlite3.connect('cs15_tutor_logs.db')
        conn.row_factory = sqlite3.Row  # This enables column access by name
        
        # Get all table names
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Found tables: {tables}")
        
        # Export each table
        export_data = {}
        total_records = 0
        
        for table in tables:
            print(f"📦 Exporting table: {table}")
            cursor = conn.execute(f"SELECT * FROM {table}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            table_data = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[columns[i]] = value
                table_data.append(row_dict)
            
            export_data[table] = table_data
            print(f"   ✅ {len(table_data)} records from {table}")
            total_records += len(table_data)
        
        conn.close()
        
        # Save to JSON file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'sqlite_backup_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"\n✅ Export completed!")
        print(f"📁 File: {filename}")
        print(f"📊 Total records: {total_records}")
        
        # Display summary
        print(f"\n📈 Export Summary:")
        for table, data in export_data.items():
            print(f"   {table}: {len(data)} records")
        
        return filename
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False

def export_using_orm():
    """Export data using the ORM (alternative method)"""
    print("📊 Exporting using ORM...")
    
    try:
        db = db_manager.get_session()
        
        # Export each model
        export_data = {}
        
        # Export Users
        users = db.query(AnonymousUser).all()
        export_data['users'] = []
        for user in users:
            export_data['users'].append({
                'id': user.id,
                'utln_hash': user.utln_hash,
                'anonymous_id': user.anonymous_id,
                'created_at': str(user.created_at),
                'last_active': str(user.last_active)
            })
        
        # Export Conversations
        conversations = db.query(Conversation).all()
        export_data['conversations'] = []
        for convo in conversations:
            export_data['conversations'].append({
                'id': convo.id,
                'conversation_id': convo.conversation_id,
                'user_id': convo.user_id,
                'platform': convo.platform,
                'created_at': str(convo.created_at),
                'last_message_at': str(convo.last_message_at),
                'message_count': convo.message_count,
                'is_active': convo.is_active
            })
        
        # Export Messages (the most important!)
        messages = db.query(Message).all()
        export_data['messages'] = []
        for msg in messages:
            export_data['messages'].append({
                'id': msg.id,
                'conversation_id': msg.conversation_id,
                'message_type': msg.message_type,
                'content': msg.content,
                'rag_context': msg.rag_context,
                'model_used': msg.model_used,
                'temperature': msg.temperature,
                'response_time_ms': msg.response_time_ms,
                'created_at': str(msg.created_at)
            })
        
        # Export Health Points
        health_points = db.query(UserHealthPoints).all()
        export_data['health_points'] = []
        for hp in health_points:
            export_data['health_points'].append({
                'id': hp.id,
                'user_id': hp.user_id,
                'current_points': hp.current_points,
                'max_points': hp.max_points,
                'last_query_at': str(hp.last_query_at) if hp.last_query_at else None,
                'last_regeneration_at': str(hp.last_regeneration_at)
            })
        
        db.close()
        
        # Save to JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'orm_backup_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        total_records = (len(export_data['users']) + 
                        len(export_data['conversations']) + 
                        len(export_data['messages']) + 
                        len(export_data['health_points']))
        
        print(f"\n✅ ORM Export completed!")
        print(f"📁 File: {filename}")
        print(f"📊 Total records: {total_records}")
        print(f"\n📈 Breakdown:")
        print(f"   Users: {len(export_data['users'])}")
        print(f"   Conversations: {len(export_data['conversations'])}")
        print(f"   Messages: {len(export_data['messages'])}")
        print(f"   Health Points: {len(export_data['health_points'])}")
        
        return filename
        
    except Exception as e:
        print(f"❌ ORM Export failed: {e}")
        return False

def display_message_preview(filename):
    """Display a preview of the student queries"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        if 'messages' in data:
            messages = data['messages']
            user_queries = [msg for msg in messages if msg['message_type'] == 'query']
            
            print(f"\n🎯 Student Query Preview ({len(user_queries)} total queries):")
            print("=" * 60)
            
            # Show first 5 queries as preview
            for i, query in enumerate(user_queries[:5]):
                print(f"\nQuery {i+1}:")
                print(f"Time: {query['created_at']}")
                print(f"Content: {query['content'][:100]}{'...' if len(query['content']) > 100 else ''}")
                print("-" * 40)
            
            if len(user_queries) > 5:
                print(f"\n... and {len(user_queries) - 5} more queries")
                
        elif 'messages' in data and isinstance(data['messages'], list):
            # Handle direct SQLite export format
            user_queries = [msg for msg in data['messages'] if msg.get('message_type') == 'query']
            print(f"\n🎯 Found {len(user_queries)} student queries in SQLite export")
            
    except Exception as e:
        print(f"❌ Preview failed: {e}")

def main():
    print("🔄 CS 15 Tutor Data Export Utility")
    print("==================================")
    
    # Try both methods
    print("\n📋 Method 1: Direct SQLite Export")
    sqlite_file = export_sqlite_to_json()
    
    print("\n📋 Method 2: ORM Export")
    orm_file = export_using_orm()
    
    # Show preview of queries
    if sqlite_file:
        display_message_preview(sqlite_file)
    elif orm_file:
        display_message_preview(orm_file)
    
    print(f"\n💾 Backup files created:")
    if sqlite_file:
        print(f"   📁 {sqlite_file}")
    if orm_file:
        print(f"   📁 {orm_file}")
    
    print(f"\n🔗 Next steps:")
    print(f"   1. Download these backup files from Render")
    print(f"   2. Switch to PostgreSQL with DATABASE_URL")
    print(f"   3. Optionally import the data to PostgreSQL")

if __name__ == "__main__":
    main() 