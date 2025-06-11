import sys
import os

# Add the api-server directory to Python path in order to import llmproxy
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'api-server'))

from llmproxy import pdf_upload


if __name__ == '__main__':
    # Define the directories to iterate through
    directories = ['admin_docs', 'hw_proj_specs', 'lab_specs']
    
    for directory in directories:
        # Check if directory exists
        if os.path.exists(directory):
            # Iterate through all files in the directory
            for filename in os.listdir(directory):
                # Check if file is a PDF
                if filename.lower().endswith('.pdf'):
                    pdf_path = os.path.join(directory, filename)
                    
                    response = pdf_upload(
                        path=pdf_path,
                        session_id='GenericSession',
                        strategy='smart')
                    
                    print(f"Uploaded {pdf_path}: {response}")
        else:
            print(f"Directory {directory} not found")
