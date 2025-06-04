import json
import requests
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')

# Read proxy config from config.json
with open(config_path, 'r') as file:
    config = json.load(file)

end_point = config['endPoint']
api_key = config['apiKey']

def retrieve(
    query: str,
    session_id: str,
    rag_threshold: float,
    rag_k: int
    ):

    headers = {
        'x-api-key': api_key,
        'request_type': 'retrieve'
    }

    request = {
        'query': query,
        'session_id': session_id,
        'rag_threshold': rag_threshold,
        'rag_k': rag_k
    }

    msg = None

    try:
        response = requests.post(end_point, headers=headers, json=request)

        if response.status_code == 200:
            msg = json.loads(response.text)
        else:
            msg = f"Error: Received response code {response.status_code}"
    except requests.exceptions.RequestException as e:
        msg = f"An error occurred: {e}"
    return msg  

def model_info():

    headers = {
        'x-api-key': api_key,
        'request_type': 'model_info'
    }

    msg = None

    try:
        response = requests.post(end_point, headers=headers, json={})

        if response.status_code == 200:
            msg = json.loads(response.text)

        else:
            msg = f"Error: Received response code {response.status_code}"
    except requests.exceptions.RequestException as e:
        msg = f"An error occurred: {e}"
    return msg  


def generate(
	model: str,
	system: str,
	query: str,
	temperature: float | None = None,
	lastk: int | None = None,
	session_id: str | None = None,
    rag_threshold: float | None = 0.5,
    rag_usage: bool | None = False,
    rag_k: int | None = 0
	):
	

    headers = {
        'x-api-key': api_key,
        'request_type': 'call'
    }

    request = {
        'model': model,
        'system': system,
        'query': query,
        'temperature': temperature,
        'lastk': lastk,
        'session_id': session_id,
        'rag_threshold': rag_threshold,
        'rag_usage': rag_usage,
        'rag_k': rag_k
    }

    msg = None

    try:
        response = requests.post(end_point, headers=headers, json=request)

        if response.status_code == 200:
            res = json.loads(response.text)
            msg = {'response':res['result'],'rag_context':res['rag_context']}
        else:
            msg = f"Error: Received response code {response.status_code}"
    except requests.exceptions.RequestException as e:
        msg = f"An error occurred: {e}"
    return msg	



def upload(multipart_form_data):

    headers = {
        'x-api-key': api_key,
        'request_type': 'add'
    }

    msg = None
    try:
        response = requests.post(end_point, headers=headers, files=multipart_form_data)
        
        if response.status_code == 200:
            msg = "Successfully uploaded. It may take a short while for the document to be added to your context"
        else:
            msg = f"Error: Received response code {response.status_code}"
    except requests.exceptions.RequestException as e:
        msg = f"An error occurred: {e}"
    
    return msg


def pdf_upload(
    path: str,    
    strategy: str | None = None,
    description: str | None = None,
    session_id: str | None = None
    ):
    
    params = {
        'description': description,
        'session_id': session_id,
        'strategy': strategy
    }

    multipart_form_data = {
        'params': (None, json.dumps(params), 'application/json'),
        'file': (None, open(path, 'rb'), "application/pdf")
    }

    response = upload(multipart_form_data)
    return response

def text_upload(
    text: str,    
    strategy: str | None = None,
    description: str | None = None,
    session_id: str | None = None
    ):
    
    params = {
        'description': description,
        'session_id': session_id,
        'strategy': strategy
    }


    multipart_form_data = {
        'params': (None, json.dumps(params), 'application/json'),
        'text': (None, text, "application/text")
    }


    response = upload(multipart_form_data)
    return response
