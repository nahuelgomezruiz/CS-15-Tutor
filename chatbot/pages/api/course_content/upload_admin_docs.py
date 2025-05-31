import sys
import os

# Add the parent directory to Python path in order to import llmproxy
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llmproxy import text_upload

# Read content from text files
def read_text_file(filename):
    """Read content from a text file in the admin_docs directory"""
    file_path = os.path.join(os.path.dirname(__file__), 'admin_docs', filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

# Load content from files
landing_page = read_text_file('landing_page.txt')
summer_2024_course_mechanics = read_text_file('course_mechanics.txt')

# Upload text content using text_upload function
if __name__ == "__main__":
    print("Uploading landing page content...")
    landing_page_response = text_upload(
        text=landing_page,
        strategy='smart',
        description='CS 15 Summer 2025 course landing page with welcome information, instructor details, and basic course information',
        session_id='GenericSession',
    )
    print(f"Landing page upload response: {landing_page_response}")

    print("\nUploading course mechanics content...")
    course_mechanics_response = text_upload(
        text=summer_2024_course_mechanics,
        strategy='smart',
        description='Detailed CS 15 Sumeer 2025 course mechanics including lectures, labs, coursework, assignments, grading policies, and course support information',
        session_id='GenericSession',
    )
    print(f"Course mechanics upload response: {course_mechanics_response}")

    print("\nBoth text uploads completed successfully!")