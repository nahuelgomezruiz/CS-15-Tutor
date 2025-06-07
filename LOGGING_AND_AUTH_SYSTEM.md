 # CS 15 Tutor - Logging and Authentication System

## Overview

This document describes the comprehensive logging and authentication system implemented for the CS 15 Tutor, which tracks user queries and responses while maintaining anonymization and conversation tracking for both the web app and VSCode extension.

## System Architecture

### Core Components

1. **Database Layer** (`responses-api-server/database.py`)
   - SQLAlchemy models for users, conversations, and messages
   - Automatic anonymization of Tufts UTLNs
   - Conversation and message tracking

2. **Authentication Service** (`responses-api-server/auth_service.py`)
   - Web app authentication via Apache .htaccess + LDAP
   - VSCode extension authentication via JWT tokens
   - Authorization checking for CS 15 students

3. **Logging Service** (`responses-api-server/logging_service.py`)
   - High-level API for logging interactions
   - User analytics and engagement tracking
   - Privacy-compliant data collection

4. **VSCode Extension Authentication** (`vscode-extension/src/authManager.ts`)
   - Token-based authentication for VSCode
   - Browser-based authentication flow
   - Secure token storage

## Database Schema

### AnonymousUser Table
- `id`: Primary key
- `utln_hash`: SHA-256 hash of the Tufts UTLN (for privacy)
- `anonymous_id`: Random identifier (e.g., "aaaaaa00")
- `created_at`: First seen timestamp
- `last_active`: Last activity timestamp

### Conversation Table
- `id`: Primary key
- `conversation_id`: UUID from frontend
- `user_id`: Foreign key to AnonymousUser
- `platform`: 'web' or 'vscode'
- `created_at`: Conversation start time
- `last_message_at`: Last message timestamp
- `message_count`: Number of messages in conversation

### Message Table
- `id`: Primary key
- `conversation_id`: Foreign key to Conversation
- `message_type`: 'query' or 'response'
- `content`: Message text
- `rag_context`: RAG context used (for responses)
- `model_used`: AI model used
- `temperature`: Model temperature setting
- `response_time_ms`: Response generation time
- `created_at`: Message timestamp

## Authentication Systems

### Web App Authentication
- Uses Apache `.htaccess` with LDAP authentication
- Authenticates against `ldap://ldap.eecs.tufts.edu`
- Authorization via `.htgrp` file listing CS 15 students
- UTLN extracted from `REMOTE_USER` environment variable

### VSCode Extension Authentication
1. **Authentication Flow:**
   - User clicks "Sign In" in extension
   - Extension requests authentication URL from API server
   - Browser opens to web authentication page
   - User authenticates via Tufts LDAP (through .htaccess)
   - Server generates JWT token and stores in session
   - Extension polls for authentication completion
   - Token stored securely in VSCode extension storage

2. **Token Management:**
   - JWT tokens expire after 24 hours
   - Tokens include UTLN and platform information
   - Automatic token refresh and re-authentication

## Privacy and Anonymization

### User Privacy Features
- **UTLN Hashing**: Original UTLNs are hashed with SHA-256
- **Anonymous IDs**: Each user gets a random anonymous identifier
- **No PII Storage**: No personally identifiable information stored
- **Secure Authentication**: Tokens are encrypted and time-limited

### Data Anonymization Process
1. User authenticates with UTLN (e.g., "jsmith01")
2. System generates SHA-256 hash of UTLN
3. System assigns random anonymous ID (e.g., "aaaaaa00")
4. All logging uses anonymous ID, not original UTLN
5. Mapping is one-way (cannot reverse engineer UTLN)

## Logging Capabilities

### Query and Response Logging
- Every user query is logged with anonymous user ID
- Assistant responses logged with metadata:
  - RAG context used
  - Model and temperature settings
  - Response generation time
  - Platform (web or VSCode)

### Conversation Tracking
- Each conversation has unique UUID
- Platform tracking (web vs VSCode)
- Message count and timing
- User engagement patterns

### Analytics Features
- **User Analytics**: Per-user conversation and message counts
- **System Analytics**: Overall usage statistics
- **Engagement Analysis**: User return rates and multi-conversation patterns
- **Platform Comparison**: Web vs VSCode usage statistics

## API Endpoints

### Authentication Endpoints
- `GET/POST /vscode-auth`: VSCode authentication handling
- `GET /vscode-auth-status`: Check authentication status

### Analytics Endpoints
- `GET /analytics`: System-wide analytics (authenticated users)

### Chat Endpoints (Enhanced)
- `POST /api`: Main chat endpoint (now requires authentication)
- `POST /api/stream`: Streaming chat with authentication

## Usage Examples

### Logging a Complete Interaction
```python
from logging_service import logging_service

# Log query and response in one call
result = logging_service.log_conversation_interaction(
    utln="jsmith01",
    conversation_id="uuid-here",
    query="What is a binary tree?",
    response="A binary tree is...",
    platform="vscode",
    rag_context="Retrieved context...",
    model_used="4o-mini",
    temperature=0.7,
    response_time_ms=1500
)

print(f"Logged for anonymous user: {result['anonymous_id']}")
```

### Getting User Analytics
```python
# Get analytics for a specific user
analytics = logging_service.get_user_statistics("jsmith01")
print(f"User has {analytics['total_conversations']} conversations")

# Get system-wide analytics
system_stats = logging_service.get_system_analytics()
print(f"Total users: {system_stats['total_users']}")
```

### Authentication in VSCode Extension
```typescript
// Check if authenticated
if (!authManager.isAuthenticated()) {
    await authManager.authenticate();
}

// Make authenticated API call
const response = await fetch('/api/stream', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${authManager.getAuthToken()}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message, conversationId })
});
```

## Security Considerations

### Authentication Security
- JWT tokens use secure signing
- Tokens have limited lifespan (24 hours)
- LDAP authentication through established Tufts infrastructure
- Authorization checking against CS 15 enrollment

### Data Security
- User UTLNs never stored in plain text
- Database uses hashed identifiers
- No reversible mapping from anonymous ID to UTLN
- Secure token transmission

### Privacy Compliance
- Data minimization (only necessary data collected)
- Purpose limitation (data used only for educational analytics)
- User transparency (logging disclosed to users)
- Anonymization prevents identification

## Deployment Considerations

### Database Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Database auto-creates on first run (SQLite by default)
3. For production, set `DATABASE_URL` environment variable

### Environment Variables
- `DATABASE_URL`: Database connection string
- `JWT_SECRET`: Secret key for JWT signing
- `CS15_AUTHORIZED_USERS`: Comma-separated list of authorized UTLNs

### Web Server Configuration
- Ensure Apache .htaccess authentication is working
- Configure LDAP connection to Tufts servers
- Update .htgrp file with authorized students

## Monitoring and Analytics

### Available Analytics
- Total users and conversations
- Active users per day/week/month
- Average messages per conversation
- Platform usage distribution (web vs VSCode)
- User return rates and engagement patterns

### Privacy-Safe Reporting
- All reports use anonymous IDs
- Aggregate statistics only
- No individual user identification possible
- Conversation content analysis without PII

## Future Enhancements

### Potential Improvements
1. **Advanced Analytics**: ML-based engagement prediction
2. **A/B Testing**: Response effectiveness comparison
3. **Performance Monitoring**: Response time tracking
4. **Content Analysis**: Common query patterns (anonymized)
5. **Federated Learning**: Model improvement without data centralization

### Scalability Considerations
- Database migration to PostgreSQL for production
- Redis session storage for VSCode authentication
- Horizontal scaling of API servers
- CDN for static authentication pages

## Troubleshooting

### Common Issues
1. **Authentication Failures**: Check LDAP connectivity and .htgrp file
2. **Token Expiry**: Users need to re-authenticate after 24 hours
3. **Database Errors**: Check SQLAlchemy connection and permissions
4. **VSCode Auth**: Ensure API server is running on correct port

### Debug Mode
Enable debug logging in Python:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Conclusion

This comprehensive logging and authentication system provides:
- **Privacy-compliant** user tracking with anonymization
- **Secure authentication** for both web and VSCode platforms
- **Detailed analytics** for educational effectiveness assessment
- **Scalable architecture** for future expansion
- **Regulatory compliance** with educational data privacy requirements

The system successfully addresses the requirements for tracking user queries and responses, distinguishing between users and conversations, while maintaining strict privacy protections through anonymization. 