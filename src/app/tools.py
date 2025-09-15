import requests
from app import config
from typing import Any, Callable, Set, Dict, List, Optional
import json


def retrieve_contract(contract_id: str, supplier_id: str) -> str:
    """
    get the contract details for the given contract_id and supplier_id

    :param contract_id (str): The contract id against which the Supplier fulfils order and raises the Purchase Invoice.
    :param supplier_id (str): The Supplier ID corresponding to the contract id.
    :return: retrieved contract details.
    :rtype: Any
    """

    api_url = config.az_logic_app_url
    print("calling Azure Logic App to get the contract details .................")
    # make a HTTP POST API call with json payload
    response = requests.post(
        api_url,
        json={"ContractID": contract_id, "SupplierID": supplier_id},
        headers={"Content-Type": "application/json"},
    )

    #print(json.dumps(json.loads(response.text), indent=4),    )
    return json.dumps(response.text)


