from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import hashlib
import secrets
import os
from typing import Optional

Base = declarative_base()

class AnonymousUser(Base):
    """Maps Tufts UTLNs to anonymous identifiers"""
    __tablename__ = 'anonymous_users'
    
    id = Column(Integer, primary_key=True)
    utln_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash of UTLN
    anonymous_id = Column(String(16), unique=True, nullable=False, index=True)  # Anonymous identifier like 'aaaaaa00'
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    
    def __repr__(self):
        return f"<AnonymousUser(anonymous_id='{self.anonymous_id}')>"

class Conversation(Base):
    """Tracks individual conversations for each user"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID from frontend
    user_id = Column(Integer, ForeignKey('anonymous_users.id'), nullable=False)
    platform = Column(String(20), default='web')  # 'web' or 'vscode'
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("AnonymousUser", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id='{self.conversation_id}', user='{self.user.anonymous_id}', platform='{self.platform}')>"

class Message(Base):
    """Stores individual messages (both queries and responses)"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    message_type = Column(String(20), nullable=False)  # 'query' or 'response'
    content = Column(Text, nullable=False)
    rag_context = Column(Text, nullable=True)  # RAG context used for the response
    model_used = Column(String(50), nullable=True)  # Model used for generation
    temperature = Column(String(10), nullable=True)  # Temperature setting
    response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_message_type_created', 'message_type', 'created_at'),
        Index('idx_conversation_created', 'conversation_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Message(type='{self.message_type}', conversation='{self.conversation_id}')>"

class UserSession(Base):
    """Tracks user session analytics"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('anonymous_users.id'), nullable=False)
    platform = Column(String(20), nullable=False)  # 'web' or 'vscode'
    session_start = Column(DateTime, default=datetime.utcnow)
    session_end = Column(DateTime, nullable=True)
    conversations_started = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    user_agent = Column(String(500), nullable=True)
    ip_hash = Column(String(64), nullable=True)  # Hashed IP for basic analytics
    
    # Relationships
    user = relationship("AnonymousUser")
    
    def __repr__(self):
        return f"<UserSession(user='{self.user.anonymous_id}', platform='{self.platform}', start='{self.session_start}')>"

class DatabaseManager:
    """Manages database operations for the logging system"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Default to SQLite for development
            database_url = os.getenv('DATABASE_URL', 'sqlite:///cs15_tutor_logs.db')
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def generate_anonymous_id(self) -> str:
        """Generate a unique anonymous ID like 'aaaaaa00'"""
        # Generate 6 random lowercase letters + 2 random digits
        letters = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(6))
        digits = ''.join(secrets.choice('0123456789') for _ in range(2))
        return letters + digits
    
    def get_or_create_anonymous_user(self, utln: str) -> AnonymousUser:
        """Get or create an anonymous user for a given UTLN"""
        db = self.get_session()
        try:
            # Hash the UTLN for privacy
            utln_hash = hashlib.sha256(utln.encode()).hexdigest()
            
            # Check if user already exists
            user = db.query(AnonymousUser).filter(AnonymousUser.utln_hash == utln_hash).first()
            
            if user:
                # Update last active time
                user.last_active = datetime.utcnow()
                db.commit()
                return user
            
            # Create new anonymous user
            while True:
                anonymous_id = self.generate_anonymous_id()
                # Ensure uniqueness
                if not db.query(AnonymousUser).filter(AnonymousUser.anonymous_id == anonymous_id).first():
                    break
            
            user = AnonymousUser(
                utln_hash=utln_hash,
                anonymous_id=anonymous_id
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
            
        finally:
            db.close()
    
    def get_or_create_conversation(self, conversation_id: str, user: AnonymousUser, platform: str = 'web') -> Conversation:
        """Get or create a conversation"""
        db = self.get_session()
        try:
            conversation = db.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()
            
            if conversation:
                return conversation
            
            # Create new conversation
            conversation = Conversation(
                conversation_id=conversation_id,
                user_id=user.id,
                platform=platform
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return conversation
            
        finally:
            db.close()
    
    def log_message(self, conversation: Conversation, message_type: str, content: str, 
                   rag_context: str = None, model_used: str = None, 
                   temperature: str = None, response_time_ms: int = None):
        """Log a message (query or response)"""
        db = self.get_session()
        try:
            message = Message(
                conversation_id=conversation.id,
                message_type=message_type,
                content=content,
                rag_context=rag_context,
                model_used=model_used,
                temperature=str(temperature) if temperature else None,
                response_time_ms=response_time_ms
            )
            db.add(message)
            
            # Update conversation stats
            conversation.last_message_at = datetime.utcnow()
            conversation.message_count += 1
            
            db.commit()
            
        finally:
            db.close()
    
    def get_user_analytics(self, user: AnonymousUser) -> dict:
        """Get analytics for a specific user"""
        db = self.get_session()
        try:
            conversations = db.query(Conversation).filter(Conversation.user_id == user.id).all()
            total_messages = db.query(Message).join(Conversation).filter(
                Conversation.user_id == user.id
            ).count()
            
            return {
                'anonymous_id': user.anonymous_id,
                'total_conversations': len(conversations),
                'total_messages': total_messages,
                'first_seen': user.created_at,
                'last_active': user.last_active,
                'average_messages_per_conversation': total_messages / len(conversations) if conversations else 0
            }
            
        finally:
            db.close()
    
    def get_system_analytics(self) -> dict:
        """Get overall system analytics"""
        db = self.get_session()
        try:
            total_users = db.query(AnonymousUser).count()
            total_conversations = db.query(Conversation).count()
            total_messages = db.query(Message).count()
            active_users_today = db.query(AnonymousUser).filter(
                AnonymousUser.last_active >= datetime.utcnow().date()
            ).count()
            
            # Platform breakdown
            web_conversations = db.query(Conversation).filter(Conversation.platform == 'web').count()
            vscode_conversations = db.query(Conversation).filter(Conversation.platform == 'vscode').count()
            
            return {
                'total_users': total_users,
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'active_users_today': active_users_today,
                'web_conversations': web_conversations,
                'vscode_conversations': vscode_conversations,
                'average_conversations_per_user': total_conversations / total_users if total_users else 0,
                'average_messages_per_conversation': total_messages / total_conversations if total_conversations else 0
            }
            
        finally:
            db.close()

# Global database manager instance
db_manager = DatabaseManager() 