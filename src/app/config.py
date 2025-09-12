import os
from dotenv import load_dotenv

load_dotenv()

tenant_id = os.getenv("tenant-id")
client_id = os.getenv("client-id")
client_secret = os.getenv("client-secret")
azure_api_key = os.getenv("azure-api-key")
azure_endpoint = os.getenv("azure-endpoint")
azure_deployment_name = os.getenv("azure-deployment-name")
azure_api_version = os.getenv("azure-api-version")
azure_vector_store_id = os.getenv("azure-vector-store-id")
az_logic_app_url = os.getenv("logicapp-url")