import sys
import os
import datetime

# Add the api-server directory to Python path in order to import llmproxy
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'responses-api-server'))

from llmproxy import pdf_upload

# Filenames and their scheduled upload dates
scheduled_uploads = {
    'proj_calcyoulater (1).pdf': '2025-06-05',
}

# The directory where your PDFs are stored
base_path = os.path.dirname(os.path.abspath(__file__))
directory = os.path.join(base_path, 'hw_proj_specs')

if __name__ == '__main__':
    today = datetime.date.today().isoformat()

    for filename, upload_date in scheduled_uploads.items():
        if upload_date == today:
            pdf_path = os.path.join(directory, filename)

            if os.path.exists(pdf_path):
                response = pdf_upload(
                    path=pdf_path,
                    session_id='TestSummer2025',
                    strategy='smart'
                )
                print(f"✅ Uploaded {filename}: {response}")
            else:
                print(f"⚠️ File not found: {pdf_path}")
        else:
            print(f"⏳ Skipping {filename}, scheduled for {upload_date}")
