from urllib import response
from app import config
from typing import Optional
from app.tools import retrieve_contract
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import base64
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=config.azure_api_key,
    api_version=config.azure_api_version,
    azure_endpoint=config.azure_endpoint,
)

tenant_id = config.tenant_id
client_id = config.client_id
client_secret =config.client_secret
scope = 'https://storage.azure.com/.default'  # Scope para Azure Storage

# 1. Obtener el token de acceso
token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
token_data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
    'scope': scope
}
token_r = requests.post(token_url, data=token_data)
access_token = token_r.json().get('access_token')


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"]
)


class UrlRequest(BaseModel):
    blobUrl: str

@app.post("/validateinvoice")
def validate_invoice(request: UrlRequest):

    
    available_functions = {
        "retrieve_contract": retrieve_contract,
    }

    def encode_image_url_to_base64(image_url, access_token):
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(image_url, headers=headers)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode("utf-8")
        else:
            raise Exception(f"Error al descargar la imagen: {response.status_code} - {response.text}")

    #image_url = "https://onelake.blob.fabric.microsoft.com/4a19ec65-14a7-40cd-9bb8-ee5571d177bb/d09710ff-3ce1-45de-8664-42a388efc856/Files/procu/Invoice-013.png"
    image_url = request.blobUrl.strip().replace('\u200b', '')
    # Encode images
    base64_image = encode_image_url_to_base64(image_url, access_token)

    tools_list = [
        {
            "type": "file_search",
            "vector_store_ids": [config.azure_vector_store_id],
            "max_num_results": 20,
        },
        {
            "type": "function",
            "name": "retrieve_contract",
            "description": "fetch contract details for the given contract_id and supplier_id",
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_id": {
                        "type": "string",
                        "description": "The contract id registered for the Supplier in the System",
                    },
                    "supplier_id": {
                        "type": "string",
                        "description": "The Supplier ID registered in the System",
                    },
                },
                "required": ["contract_id", "supplier_id"],
            },
        },
    ]

    instructions = """
    This is a Procure to Pay process. You will be provided with the Purchase Invoice image as input.
    Note that Step 3 can be performed only after Step 1 and Step 2 are completed.
    Step 1: As a first step, you will extract the Contract ID and Supplier ID from the Purchase Invoice image along with all the line items from the Invoice in the form of a table.
    Step 2: You will then use the function tool by passing the Contract ID and Supplier ID to retrieve the contract details.
    Step 3: You will then use the file search tool to retrieve the business rules applicable to detection of anomalies in the Procure to Pay process.
    Step 4: Then, apply the retrieved business rules to match the invoice line items with the contract details fetched from the system, and detect anomalies if any.
    Provide the list of anomalies detected in the Invoice, and the business rules that were violated.
    """

    user_prompt = """
    here are the Purchase Invoice image(s) as input. Detect anomalies in the procure to pay process and give me a detailed report
    """

    input_messages = [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": user_prompt},
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high",
                }
                ,
            ],
        }
    ]

    # The following code is to call the Responses API with the input messages and tools
    response = client.responses.create(
        model=config.azure_deployment_name,
        instructions=instructions,
        input=input_messages,
        tools=tools_list,
        tool_choice="auto",
        parallel_tool_calls=False,
    )
    tool_call = response.output[0]

    function_response = None
    function_to_call = None
    function_name = None

    # When a function call is entailed, Responses API gives us control so that we can make the call from our application.
    # Note that this is because function call is to run our own custom code, it is not a hosted tool that Responses API can directly access and run.
    if response.output[0].type == "function_call":
        function_name = response.output[0].name
        function_to_call = available_functions[function_name]
        function_args = json.loads(response.output[0].arguments)
        # Lets call the Logic app with the function arguments to get the contract details.
        function_response = function_to_call(**function_args)

    # append the response message to the input messages, and proceed with the next call to the Responses API.
    input_messages.append(tool_call)  # append model's function call message
    input_messages.append(
        {  # append result message
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": str(function_response),
        }
    )

    response_2 = client.responses.create(
    model=config.azure_deployment_name,
    instructions=instructions,
    input=input_messages,
    tools=tools_list,
    tool_choice="auto",
    )
    print(f"**********Original Invoice from:{image_url}")
    print(response_2.output_text)

    def custom_serializer(obj):
        if isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)

    #return [{**vars(album), "blobUrl": request.blobUrl} for album in albums]
    return json.dumps(response_2, default=custom_serializer, indent=4)