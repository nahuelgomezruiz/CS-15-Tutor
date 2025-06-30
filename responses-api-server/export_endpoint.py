#!/usr/bin/env python3
"""
Web endpoint to export SQLite data
Add this to your main Flask app or run as standalone
"""

from flask import Flask, jsonify, send_file
import os
import json
from datetime import datetime
from export_sqlite_data import export_sqlite_to_json, export_using_orm

app = Flask(__name__)

@app.route('/admin/export-data', methods=['GET'])
def export_data():
    """Export SQLite data and return download link"""
    try:
        print("🔄 Starting data export...")
        
        # Try both export methods
        sqlite_file = export_sqlite_to_json()
        orm_file = export_using_orm()
        
        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "files": []
        }
        
        if sqlite_file:
            result["files"].append({
                "type": "sqlite_direct",
                "filename": sqlite_file,
                "size": os.path.getsize(sqlite_file) if os.path.exists(sqlite_file) else 0
            })
        
        if orm_file:
            result["files"].append({
                "type": "orm_export", 
                "filename": orm_file,
                "size": os.path.getsize(orm_file) if os.path.exists(orm_file) else 0
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/admin/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download exported file"""
    try:
        if os.path.exists(filename):
            return send_file(filename, as_attachment=True)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/check-database', methods=['GET'])
def check_database():
    """Check what data exists in current database"""
    try:
        from database import db_manager, AnonymousUser, Conversation, Message
        
        db = db_manager.get_session()
        
        # Count records
        user_count = db.query(AnonymousUser).count()
        conversation_count = db.query(Conversation).count()
        message_count = db.query(Message).count()
        
        # Count query vs response messages
        query_count = db.query(Message).filter(Message.message_type == 'query').count()
        response_count = db.query(Message).filter(Message.message_type == 'response').count()
        
        db.close()
        
        return jsonify({
            "database_type": "SQLite" if "sqlite" in str(db_manager.engine.url) else "PostgreSQL",
            "database_file_exists": os.path.exists('cs15_tutor_logs.db'),
            "counts": {
                "users": user_count,
                "conversations": conversation_count,
                "total_messages": message_count,
                "student_queries": query_count,
                "ai_responses": response_count
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 