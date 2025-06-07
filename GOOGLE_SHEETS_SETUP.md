# Google Sheets Integration Setup Guide

## 🎯 **Overview**

This guide shows you how to connect your CS 15 Tutor database to Google Sheets for real-time analytics, reporting, and data visualization.

## 📊 **What You'll Get**

- **Real-time dashboard** with user engagement metrics
- **Automated data sync** from SQLite to Google Sheets
- **Multiple worksheets**: Overview, Users, Conversations, Messages, Analytics
- **Privacy-compliant** data export (anonymous IDs only)
- **Scheduled sync** capability for continuous updates

---

## 🔧 **Step 1: Install Dependencies**

```bash
cd responses-api-server
pip install -r requirements_sheets.txt
```

This installs:
- `google-auth` - Authentication with Google APIs
- `google-api-python-client` - Google Sheets API client
- `google-auth-oauthlib` - OAuth2 flow for authentication

---

## 🏗️ **Step 2: Google Cloud Console Setup**

### **2.1 Create Google Cloud Project**

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **"Select a project"** → **"New Project"**
3. Name it **"CS 15 Tutor Analytics"**
4. Click **"Create"**

### **2.2 Enable Google Sheets API**

1. In your project, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Sheets API"**
3. Click on it and press **"Enable"**

### **2.3 Create OAuth 2.0 Credentials**

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ Create Credentials"** → **"OAuth 2.0 Client ID"**
3. If prompted, configure **OAuth consent screen**:
   - Choose **"External"** (unless you have Google Workspace)
   - App name: **"CS 15 Tutor Analytics"**
   - User support email: Your email
   - Add your email to test users
   - Save and continue through all steps
4. Back to credentials:
   - Application type: **"Desktop application"**
   - Name: **"CS 15 Tutor Desktop"**
   - Click **"Create"**

### **2.4 Download Credentials**

1. Click the **download button** (⬇️) next to your new credential
2. Save the file as **`credentials.json`** in the `responses-api-server` directory

---

## 🚀 **Step 3: Initial Setup and Authentication**

```bash
cd responses-api-server
python google_sheets_sync.py setup
```

This will:
1. ✅ Verify your `credentials.json` file
2. 🌐 Open your browser for Google authentication
3. 📊 Create a new spreadsheet with 5 worksheets
4. 🔄 Perform initial data sync
5. 💾 Save configuration to `sheets_config.json`

**Expected output:**
```
🔧 Google Sheets Setup for CS 15 Tutor
=====================================
✅ Successfully authenticated with Google Sheets API
📊 Creating new spreadsheet...
✅ Created spreadsheet: CS 15 Tutor Analytics Dashboard
📊 Spreadsheet ID: 1ABC...XYZ
🔗 URL: https://docs.google.com/spreadsheets/d/1ABC...XYZ
🔄 Starting full sync to Google Sheets...
📊 Syncing overview data...
✅ Updated Overview: 45 cells
👥 Syncing users data...
✅ Updated Users: 12 cells
💬 Syncing conversations data...
✅ Updated Conversations: 14 cells
📝 Syncing messages summary...
✅ Updated Messages: 21 cells
📈 Syncing analytics data...
✅ Updated Analytics: 32 cells
✅ Full sync completed!
🔗 View spreadsheet: https://docs.google.com/spreadsheets/d/1ABC...XYZ
```

---

## 📊 **Step 4: Understanding Your Spreadsheet**

Your new Google Spreadsheet will have 5 worksheets:

### **Overview Sheet**
- Total users, conversations, messages
- Platform distribution (Web vs VSCode)
- Recent activity (7-day window)
- High-level metrics with descriptions

### **Users Sheet**
- Anonymous user IDs (e.g., `jlrgem54`)
- Creation dates and last activity
- Days since created/last active
- User engagement patterns

### **Conversations Sheet**
- Individual chat sessions
- Platform used (web/vscode)
- Duration and message counts
- Timeline data

### **Messages Sheet**
- Message metadata (NOT content for privacy)
- Timestamps and response times
- Model used and content length
- Platform and user associations

### **Analytics Sheet**
- Time-based breakdowns (24h, 7d, 30d)
- Average response times
- Platform usage statistics
- Engagement trends

---

## 🔄 **Step 5: Regular Data Sync**

### **Manual Sync Commands**

```bash
# Full sync (all data)
python google_sheets_sync.py sync

# Sync specific sheets only
python google_sheets_sync.py overview
python google_sheets_sync.py users
python google_sheets_sync.py messages
```

### **Automated Sync (Optional)**

Create a batch file for Windows or shell script for Mac/Linux:

**Windows (`sync_sheets.bat`):**
```batch
@echo off
cd /d "C:\path\to\CS-15-Tutor\responses-api-server"
python google_sheets_sync.py sync
echo Sync completed at %date% %time%
```

**Mac/Linux (`sync_sheets.sh`):**
```bash
#!/bin/bash
cd "/path/to/CS-15-Tutor/responses-api-server"
python google_sheets_sync.py sync
echo "Sync completed at $(date)"
```

**Schedule with Task Scheduler (Windows) or Cron (Mac/Linux):**
- Run every hour: `0 * * * *`
- Run daily at 6 AM: `0 6 * * *`
- Run every 15 minutes: `*/15 * * * *`

---

## 📈 **Step 6: Creating Charts and Dashboards**

### **In Google Sheets:**

1. **Select your data range** (e.g., Analytics sheet)
2. **Insert** → **Chart**
3. **Chart types to try:**
   - **Line chart**: User activity over time
   - **Pie chart**: Platform distribution
   - **Bar chart**: Messages per user
   - **Area chart**: Cumulative usage trends

### **Advanced Analytics:**

1. **Pivot Tables** for custom analysis
2. **Conditional formatting** for highlighting trends
3. **Data validation** for dropdown filters
4. **IMPORTRANGE** to combine with other sheets

---

## 🔒 **Privacy and Security**

### **What's Synced:**
✅ Anonymous user IDs (e.g., `jlrgem54`)  
✅ Conversation metadata  
✅ Message timestamps and lengths  
✅ Response times and models used  
✅ Platform usage statistics  

### **What's NOT Synced:**
❌ Real usernames/UTLNs  
❌ Actual message content  
❌ Personal information  
❌ Raw database IDs  

### **Security Best Practices:**
- 🔐 Keep `credentials.json` secure
- 🚫 Don't share spreadsheet publicly
- 📊 Only share with authorized CS 15 staff
- 🔄 Regularly review access permissions

---

## 🛠️ **Troubleshooting**

### **"credentials.json not found"**
- Download credentials from Google Cloud Console
- Ensure file is named exactly `credentials.json`
- Place in `responses-api-server` directory

### **"Authentication failed"**
- Check OAuth consent screen is configured
- Ensure your email is added as test user
- Try deleting `token.json` and re-authenticating

### **"Spreadsheet not found"**
- Check `sheets_config.json` has correct spreadsheet ID
- Verify spreadsheet wasn't deleted
- Run setup again to create new spreadsheet

### **"Missing database"**
- Ensure `cs15_tutor_logs.db` exists
- Run the API server to create initial data
- Check database has data with `python simple_data_export.py show`

### **API quota exceeded**
- Google Sheets API has usage limits
- Wait a few minutes before retrying
- Consider reducing sync frequency

---

## 📊 **Example Use Cases**

### **For Instructors:**
- **Track student engagement** with the tutor system
- **Monitor peak usage times** for office hours planning
- **Compare web vs VSCode adoption** rates
- **Identify highly active students** for follow-up

### **For TAs:**
- **Response time analysis** to improve system performance
- **Common question patterns** from message metadata
- **Platform preferences** by student type
- **Usage trends** over the semester

### **For Administrators:**
- **System utilization** metrics for resource planning
- **Anonymized usage reports** for stakeholders
- **Performance monitoring** and optimization
- **Student privacy compliance** reporting

---

## 🔧 **Advanced Configuration**

### **Custom Sync Intervals**
Edit the sync script to change data refresh frequency:

```python
# In google_sheets_sync.py, modify the sync_analytics_data function
periods = [
    ("Last 6 hours", 0.25),    # More granular
    ("Last 24 hours", 1),      
    ("Last 3 days", 3),        # Custom periods
    ("Last 7 days", 7),
    ("Last 30 days", 30)
]
```

### **Additional Metrics**
Add custom metrics by modifying the sync functions:

```python
# Example: Add average session length
avg_session_duration = db.query(
    func.avg(func.julianday(Conversation.last_message_at) - 
             func.julianday(Conversation.created_at)) * 24 * 60
).scalar() or 0
```

### **Multiple Spreadsheets**
Create separate spreadsheets for different purposes:
- Weekly reports
- Monthly summaries  
- Instructor dashboards
- Administrative reports

---

## ✅ **Success Checklist**

- [ ] Google Cloud project created
- [ ] Google Sheets API enabled
- [ ] OAuth credentials downloaded as `credentials.json`
- [ ] Dependencies installed (`pip install -r requirements_sheets.txt`)
- [ ] Authentication completed (`python google_sheets_sync.py setup`)
- [ ] Spreadsheet created and accessible
- [ ] Initial data sync successful
- [ ] Charts and dashboards configured
- [ ] Regular sync schedule established (optional)

**🎉 Congratulations! Your CS 15 Tutor database is now connected to Google Sheets for powerful analytics and reporting!**

---

## 📞 **Support**

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all setup steps were completed
3. Test with sample commands
4. Review Google Cloud Console configuration
5. Check database has data to sync

**Ready to analyze your CS 15 Tutor usage data!** 📊 