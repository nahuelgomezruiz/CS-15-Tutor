#!/usr/bin/env python3
"""
Google Sheets Sync for CS 15 Tutor Database

This script syncs anonymized data from the CS 15 Tutor database to Google Sheets
for easy analysis and reporting.

Setup Requirements:
1. Install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
2. Create Google Cloud Project and enable Sheets API
3. Download credentials.json file
4. Run this script to authenticate and sync data
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ Missing Google API libraries. Please install:")
    print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    exit(1)

from database import db_manager, AnonymousUser, Conversation, Message, UserSession

# Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Google Sheets configuration
SPREADSHEET_ID = None  # Will be set during setup
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

class GoogleSheetsSync:
    """Handles syncing CS 15 Tutor data to Google Sheets"""
    
    def __init__(self, spreadsheet_id: str = None):
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        creds = None
        
        # Load existing token
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    print(f"❌ {CREDENTIALS_FILE} not found!")
                    print("Please download credentials from Google Cloud Console:")
                    print("1. Go to https://console.cloud.google.com")
                    print("2. Create project & enable Google Sheets API") 
                    print("3. Create OAuth 2.0 credentials")
                    print("4. Download as 'credentials.json'")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('sheets', 'v4', credentials=creds)
            print("✅ Successfully authenticated with Google Sheets API")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Google Sheets API: {e}")
            return False
    
    def create_spreadsheet(self, title: str = "CS 15 Tutor Analytics") -> str:
        """Create a new Google Spreadsheet"""
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': [
                    {'properties': {'title': 'Overview'}},
                    {'properties': {'title': 'Users'}},
                    {'properties': {'title': 'Conversations'}},
                    {'properties': {'title': 'Messages'}},
                    {'properties': {'title': 'Analytics'}},
                    {'properties': {'title': 'DetailedConversations'}},
                    {'properties': {'title': 'RAGAnalysis'}},
                    {'properties': {'title': 'UserInteractions'}}
                ]
            }
            
            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result.get('spreadsheetId')
            
            print(f"✅ Created spreadsheet: {title}")
            print(f"📊 Spreadsheet ID: {spreadsheet_id}")
            print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            
            return spreadsheet_id
            
        except HttpError as e:
            print(f"❌ Error creating spreadsheet: {e}")
            return None
    
    def ensure_sheet_exists(self, sheet_name: str):
        """Ensure a sheet exists, create it if it doesn't"""
        try:
            # Get spreadsheet metadata to check existing sheets
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]
            
            if sheet_name not in existing_sheets:
                print(f"📄 Creating missing sheet: {sheet_name}")
                # Add the new sheet
                requests = [{
                    "addSheet": {
                        "properties": {
                            "title": sheet_name
                        }
                    }
                }]
                
                body = {"requests": requests}
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                print(f"✅ Created sheet: {sheet_name}")
                
        except HttpError as e:
            print(f"❌ Error ensuring sheet {sheet_name} exists: {e}")

    def clear_sheet(self, sheet_name: str):
        """Clear all data from a sheet"""
        try:
            # Ensure sheet exists first
            self.ensure_sheet_exists(sheet_name)
            
            range_name = f"{sheet_name}!A:Z"
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
        except HttpError as e:
            print(f"❌ Error clearing sheet {sheet_name}: {e}")
    
    def write_to_sheet(self, sheet_name: str, data: List[List], start_cell: str = "A1"):
        """Write data to a specific sheet"""
        try:
            # Ensure sheet exists first
            self.ensure_sheet_exists(sheet_name)
            
            range_name = f"{sheet_name}!{start_cell}"
            body = {
                'values': data
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"✅ Updated {sheet_name}: {result.get('updatedCells')} cells")
            
        except HttpError as e:
            print(f"❌ Error writing to sheet {sheet_name}: {e}")
    
    def sync_overview_data(self):
        """Sync system overview to Overview sheet"""
        print("📊 Syncing overview data...")
        
        db = db_manager.get_session()
        try:
            # Get basic stats
            total_users = db.query(AnonymousUser).count()
            total_conversations = db.query(Conversation).count() 
            total_messages = db.query(Message).count()
            
            # Platform breakdown
            web_convos = db.query(Conversation).filter(Conversation.platform == 'web').count()
            vscode_convos = db.query(Conversation).filter(Conversation.platform == 'vscode').count()
            
            # Recent activity
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_users = db.query(AnonymousUser).filter(AnonymousUser.last_active >= week_ago).count()
            recent_messages = db.query(Message).filter(Message.created_at >= week_ago).count()
            
            # Prepare data for sheets
            data = [
                ["CS 15 Tutor System Overview", f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
                [""],
                ["Metric", "Value", "Description"],
                ["Total Users", total_users, "Anonymous users who have used the system"],
                ["Total Conversations", total_conversations, "Individual chat sessions"],
                ["Total Messages", total_messages, "All queries and responses"],
                ["Web Conversations", web_convos, "Conversations via web app"],
                ["VSCode Conversations", vscode_convos, "Conversations via VSCode extension"],
                ["Active Users (7 days)", recent_users, "Users active in the last week"],
                ["Recent Messages (7 days)", recent_messages, "Messages sent in the last week"],
                [""],
                ["Platform Distribution"],
                ["Platform", "Conversations", "Percentage"],
                ["Web", web_convos, f"{(web_convos/total_conversations*100):.1f}%" if total_conversations > 0 else "0%"],
                ["VSCode", vscode_convos, f"{(vscode_convos/total_conversations*100):.1f}%" if total_conversations > 0 else "0%"]
            ]
            
            self.clear_sheet("Overview")
            self.write_to_sheet("Overview", data)
            
        finally:
            db.close()
    
    def sync_users_data(self):
        """Sync user data to Users sheet"""
        print("👥 Syncing users data...")
        
        db = db_manager.get_session()
        try:
            users = db.query(AnonymousUser).all()
            
            # Headers
            data = [
                ["Anonymous ID", "Created At", "Last Active", "Days Since Created", "Days Since Last Active"]
            ]
            
            # User data
            now = datetime.utcnow()
            for user in users:
                days_since_created = (now - user.created_at).days
                days_since_active = (now - user.last_active).days
                
                data.append([
                    user.anonymous_id,
                    user.created_at.strftime('%Y-%m-%d %H:%M'),
                    user.last_active.strftime('%Y-%m-%d %H:%M'),
                    days_since_created,
                    days_since_active
                ])
            
            self.clear_sheet("Users")
            self.write_to_sheet("Users", data)
            
        finally:
            db.close()
    
    def sync_conversations_data(self):
        """Sync conversation data to Conversations sheet"""
        print("💬 Syncing conversations data...")
        
        db = db_manager.get_session()
        try:
            conversations = db.query(Conversation).all()
            
            # Headers
            data = [
                ["User ID", "Platform", "Created At", "Last Message", "Message Count", "Duration (minutes)"]
            ]
            
            # Conversation data
            for convo in conversations:
                duration = (convo.last_message_at - convo.created_at).total_seconds() / 60
                
                data.append([
                    convo.user.anonymous_id,
                    convo.platform,
                    convo.created_at.strftime('%Y-%m-%d %H:%M'),
                    convo.last_message_at.strftime('%Y-%m-%d %H:%M'),
                    convo.message_count,
                    round(duration, 1)
                ])
            
            self.clear_sheet("Conversations")
            self.write_to_sheet("Conversations", data)
            
        finally:
            db.close()
    
    def sync_messages_summary(self):
        """Sync message summary to Messages sheet"""
        print("📝 Syncing messages summary...")
        
        db = db_manager.get_session()
        try:
            messages = db.query(Message).all()
            
            # Headers
            data = [
                ["Timestamp", "User ID", "Platform", "Type", "Content Length", "Model", "Response Time (ms)"]
            ]
            
            # Message data (summary only for privacy)
            for msg in messages:
                convo = msg.conversation
                
                data.append([
                    msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    convo.user.anonymous_id,
                    convo.platform,
                    msg.message_type,
                    len(msg.content),
                    msg.model_used or 'N/A',
                    msg.response_time_ms or 0
                ])
            
            self.clear_sheet("Messages")
            self.write_to_sheet("Messages", data)
            
        finally:
            db.close()
    
    def sync_analytics_data(self):
        """Sync advanced analytics to Analytics sheet"""
        print("📈 Syncing analytics data...")
        
        db = db_manager.get_session()
        try:
            # Time-based analytics
            periods = [
                ("Last 24 hours", 1),
                ("Last 7 days", 7),
                ("Last 30 days", 30)
            ]
            
            data = [
                ["CS 15 Tutor Analytics Dashboard"],
                [""],
                ["Time Period", "Active Users", "New Conversations", "Total Messages", "Avg Response Time (ms)"]
            ]
            
            for period_name, days in periods:
                cutoff = datetime.utcnow() - timedelta(days=days)
                
                active_users = db.query(AnonymousUser).filter(AnonymousUser.last_active >= cutoff).count()
                new_conversations = db.query(Conversation).filter(Conversation.created_at >= cutoff).count()
                total_messages = db.query(Message).filter(Message.created_at >= cutoff).count()
                
                # Average response time
                avg_response = db.query(Message.response_time_ms).filter(
                    Message.created_at >= cutoff,
                    Message.response_time_ms.isnot(None)
                ).all()
                
                avg_ms = sum(r[0] for r in avg_response) / len(avg_response) if avg_response else 0
                
                data.append([
                    period_name,
                    active_users,
                    new_conversations,
                    total_messages,
                    round(avg_ms, 0)
                ])
            
            # Add platform usage
            data.extend([
                [""],
                ["Platform Usage"],
                ["Platform", "Total Conversations", "Unique Users"]
            ])
            
            platforms = ['web', 'vscode']
            for platform in platforms:
                platform_convos = db.query(Conversation).filter(Conversation.platform == platform).count()
                platform_users = db.query(AnonymousUser).join(Conversation).filter(
                    Conversation.platform == platform
                ).distinct().count()
                
                data.append([platform.title(), platform_convos, platform_users])
            
            self.clear_sheet("Analytics")
            self.write_to_sheet("Analytics", data)
            
        finally:
            db.close()
    
    def sync_detailed_conversations(self):
        """Sync detailed conversation threads with full content and RAG context"""
        print("🔍 Syncing detailed conversations with full content...")
        
        db = db_manager.get_session()
        try:
            conversations = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
            
            # Headers
            data = [
                ["Conversation Details - Full Content and RAG Context"],
                [""],
                ["User ID", "Platform", "Conversation Start", "Message #", "Timestamp", "Type", "Content", "RAG Context", "Model", "Response Time (ms)", "Content Length"]
            ]
            
            for convo in conversations:
                # Get all messages for this conversation
                messages = db.query(Message).filter(
                    Message.conversation_id == convo.id
                ).order_by(Message.created_at.asc()).all()
                
                # Add conversation header
                data.append([
                    f"=== CONVERSATION: {convo.user.anonymous_id} ===",
                    convo.platform,
                    convo.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    f"Duration: {((convo.last_message_at - convo.created_at).total_seconds() / 60):.1f} min",
                    f"Messages: {len(messages)}",
                    "",
                    "",
                    "",
                    "",
                    "",
                    ""
                ])
                
                # Add each message
                for i, msg in enumerate(messages, 1):
                    # Truncate very long content for sheet readability
                    content = msg.content
                    if len(content) > 500:
                        content = content[:500] + "... [TRUNCATED]"
                    
                    # Truncate RAG context
                    rag_context = msg.rag_context or "No RAG context"
                    if len(rag_context) > 300:
                        rag_context = rag_context[:300] + "... [TRUNCATED]"
                    
                    data.append([
                        convo.user.anonymous_id,
                        convo.platform,
                        convo.created_at.strftime('%Y-%m-%d %H:%M'),
                        f"Msg {i}",
                        msg.created_at.strftime('%H:%M:%S'),
                        msg.message_type.upper(),
                        content,
                        rag_context,
                        msg.model_used or 'N/A',
                        msg.response_time_ms or 0,
                        len(msg.content)
                    ])
                
                # Add separator between conversations
                data.append(["", "", "", "", "", "", "", "", "", "", ""])
            
            self.clear_sheet("DetailedConversations")
            self.write_to_sheet("DetailedConversations", data)
            
        finally:
            db.close()
    
    def sync_rag_context_analysis(self):
        """Sync RAG context analysis for understanding what content is being retrieved"""
        print("🧠 Syncing RAG context analysis...")
        
        db = db_manager.get_session()
        try:
            # Get all messages with RAG context
            messages_with_rag = db.query(Message).filter(
                Message.rag_context.isnot(None),
                Message.message_type == 'response'
            ).order_by(Message.created_at.desc()).all()
            
            data = [
                ["RAG Context Analysis"],
                [""],
                ["Timestamp", "User ID", "Platform", "Query", "Response Preview", "RAG Context Preview", "Model", "Response Time (ms)"]
            ]
            
            for msg in messages_with_rag:
                convo = msg.conversation
                
                # Find the corresponding query message
                query_msg = db.query(Message).filter(
                    Message.conversation_id == convo.id,
                    Message.message_type == 'query',
                    Message.created_at < msg.created_at
                ).order_by(Message.created_at.desc()).first()
                
                query_content = query_msg.content if query_msg else "No query found"
                if len(query_content) > 100:
                    query_content = query_content[:100] + "..."
                
                response_preview = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
                rag_preview = msg.rag_context[:200] + "..." if len(msg.rag_context) > 200 else msg.rag_context
                
                data.append([
                    msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    convo.user.anonymous_id,
                    convo.platform,
                    query_content,
                    response_preview,
                    rag_preview,
                    msg.model_used or 'N/A',
                    msg.response_time_ms or 0
                ])
            
            self.clear_sheet("RAGAnalysis")
            self.write_to_sheet("RAGAnalysis", data)
            
        finally:
            db.close()
    
    def sync_user_interactions(self):
        """Sync user interactions showing Query -> RAG Context -> Response for each user"""
        print("👤 Syncing user interactions (Query -> RAG -> Response)...")
        
        db = db_manager.get_session()
        try:
            # Get all conversations ordered by most recent
            conversations = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
            
            data = [
                ["User Interactions - Queries, RAG Context, and Responses"],
                [""],
                ["User ID", "Platform", "Conversation Date", "Turn #", "User Query", "RAG Context Retrieved", "Model Response", "Response Time (ms)", "Query Length", "Response Length"]
            ]
            
            for convo in conversations:
                # Get all messages for this conversation
                messages = db.query(Message).filter(
                    Message.conversation_id == convo.id
                ).order_by(Message.created_at.asc()).all()
                
                # Group messages into query-response pairs
                query_msg = None
                turn_number = 0
                
                for msg in messages:
                    if msg.message_type == 'query':
                        query_msg = msg
                        turn_number += 1
                    elif msg.message_type == 'response' and query_msg:
                        # We have a query-response pair
                        query_content = query_msg.content
                        response_content = msg.content
                        rag_context = msg.rag_context or "No RAG context retrieved"
                        
                        # Truncate very long content for readability
                        if len(query_content) > 200:
                            query_content = query_content[:200] + "... [TRUNCATED]"
                        if len(response_content) > 300:
                            response_content = response_content[:300] + "... [TRUNCATED]" 
                        if len(rag_context) > 400:
                            rag_context = rag_context[:400] + "... [TRUNCATED]"
                        
                        data.append([
                            convo.user.anonymous_id,
                            convo.platform,
                            convo.created_at.strftime('%Y-%m-%d %H:%M'),
                            f"Turn {turn_number}",
                            query_content,
                            rag_context,
                            response_content,
                            msg.response_time_ms or 0,
                            len(query_msg.content),
                            len(msg.content)
                        ])
                        
                        query_msg = None  # Reset for next pair
                
                # Add separator between conversations  
                if messages:  # Only add separator if conversation had messages
                    data.append(["---", "---", "---", "---", "---", "---", "---", "---", "---", "---"])
            
            self.clear_sheet("UserInteractions")
            self.write_to_sheet("UserInteractions", data)
            
        finally:
            db.close()
    
    def full_sync(self):
        """Perform a complete sync of all data"""
        print("🔄 Starting full sync to Google Sheets...")
        
        if not self.service:
            print("❌ Not authenticated with Google Sheets API")
            return False
        
        if not self.spreadsheet_id:
            print("❌ No spreadsheet ID configured")
            return False
        
        try:
            self.sync_overview_data()
            self.sync_users_data()
            self.sync_conversations_data()
            self.sync_messages_summary()
            self.sync_analytics_data()
            self.sync_user_interactions()  # This is what the user wants to see!
            self.sync_detailed_conversations()
            self.sync_rag_context_analysis()
            
            print(f"✅ Full sync completed!")
            print(f"🔗 View spreadsheet: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
            return True
            
        except Exception as e:
            print(f"❌ Sync failed: {e}")
            return False

def setup_google_sheets():
    """Interactive setup for Google Sheets integration"""
    print("🔧 Google Sheets Setup for CS 15 Tutor")
    print("=====================================")
    
    # Check for credentials
    if not os.path.exists(CREDENTIALS_FILE):
        print("\n📋 Setup Steps:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create a new project or select existing")
        print("3. Enable the Google Sheets API")
        print("4. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client ID'")
        print("5. Choose 'Desktop Application'")
        print("6. Download the JSON file and rename it to 'credentials.json'")
        print("7. Place credentials.json in this directory")
        print("\nRun this script again after completing these steps.")
        return
    
    # Create spreadsheet
    sync = GoogleSheetsSync()
    if not sync.service:
        return
    
    print("\n📊 Creating new spreadsheet...")
    spreadsheet_id = sync.create_spreadsheet("CS 15 Tutor Analytics Dashboard")
    
    if spreadsheet_id:
        # Save spreadsheet ID
        config = {"spreadsheet_id": spreadsheet_id}
        with open("sheets_config.json", "w") as f:
            json.dump(config, f)
        
        # Perform initial sync
        sync.spreadsheet_id = spreadsheet_id
        sync.full_sync()
        
        print(f"\n✅ Setup complete!")
        print(f"📄 Config saved to sheets_config.json")
        print(f"🔗 Spreadsheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        print("Google Sheets Sync for CS 15 Tutor Database")
        print("\nCommands:")
        print("  python google_sheets_sync.py setup       - Initial setup")
        print("  python google_sheets_sync.py sync        - Full sync")
        print("  python google_sheets_sync.py overview    - Sync overview only")
        print("  python google_sheets_sync.py users       - Sync users only")
        print("  python google_sheets_sync.py messages    - Sync messages only")
        print("  python google_sheets_sync.py detailed    - Sync detailed conversations")
        print("  python google_sheets_sync.py rag         - Sync RAG context analysis")
        return
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        setup_google_sheets()
        return
    
    # Load existing config
    if not os.path.exists("sheets_config.json"):
        print("❌ No configuration found. Run setup first:")
        print("python google_sheets_sync.py setup")
        return
    
    with open("sheets_config.json", "r") as f:
        config = json.load(f)
    
    spreadsheet_id = config.get("spreadsheet_id")
    if not spreadsheet_id:
        print("❌ No spreadsheet ID in config")
        return
    
    sync = GoogleSheetsSync(spreadsheet_id)
    
    if command == "sync":
        sync.full_sync()
    elif command == "overview":
        sync.sync_overview_data()
    elif command == "users":
        sync.sync_users_data()
    elif command == "messages":
        sync.sync_messages_summary()
    elif command == "detailed":
        sync.sync_detailed_conversations()
    elif command == "rag":
        sync.sync_rag_context_analysis()
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main() 