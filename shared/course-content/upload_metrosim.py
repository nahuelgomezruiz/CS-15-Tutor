import sys
import os

# Add the api-server directory to Python path in order to import llmproxy
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'responses-api-server'))

from llmproxy import pdf_upload

# The directory where your PDFs are stored
base_path = os.path.dirname(os.path.abspath(__file__))
directory = os.path.join(base_path, 'hw_proj_specs')

if __name__ == '__main__':
    filename = "proj_metrosim (2).pdf"
    pdf_path = os.path.join(directory, filename)
    if os.path.exists(pdf_path):
        response = pdf_upload(
            path=pdf_path,
            session_id='MetrosimTestSession',
            strategy='smart'
        )
        print(f"✅ Uploaded {filename}: {response}")
    else:
        print(f"⚠️ File not found: {pdf_path}")
