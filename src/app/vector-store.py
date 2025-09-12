from app import config
from openai import AzureOpenAI
import json

# Asegúrate de tener en config.py:
# azure_api_key, azure_endpoint, azure_deployment_name, azure_api_version, azure_vector_store_id

client = AzureOpenAI(
    api_key=config.azure_api_key,
    api_version=config.azure_api_version,
    azure_endpoint=config.azure_endpoint,
)


#vector_store = client.vector_stores.create(name="BusinessRules")
#print(vector_store)

# test the vector store

response = client.responses.create(
    model=config.azure_deployment_name,  # Nombre del deployment en Azure OpenAI
    tools=[{
      "type": "file_search",
      "vector_store_ids": [config.azure_vector_store_id],
      "max_num_results": 20
    }],
    input="What are business rules in procure to pay process?",
    )


print(json.dumps(response, default=lambda o: o.__dict__, indent=4))
