import requests
import json
import logging
from config import cfg
from web3 import Web3, HTTPProvider
import eth_api.test_data as test_data
from time import sleep

logger = logging.getLogger('root')
logger.debug('loading')

DefaultErrorMessage = {"error": "Something went wrong, please contact tusc support"}

ErrorCodeSuccess = 0
ErrorCodeFailedWithResponse = 1
ErrorCodeFailedMethodNameResponse = 2

eth_api_cfg = cfg["eth_api"]
general_cfg = cfg["general"]

swapper_contract_abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "last_occ_balance",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "tusc_address",
                "type": "string"
            }
        ],
        "name": "doSwap",
        "outputs": [
            {
                "name": "success",
                "type": "bool"
            }
        ],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "occ_token",
        "outputs": [
            {
                "name": "",
                "type": "address"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "tokens_swapped",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "swaps_attempted",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "total_tokens",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "name": "_omega_address",
                "type": "address"
            },
            {
                "name": "_occ_contract_address",
                "type": "address"
            }
        ],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "constructor"
    }
]

w3 = Web3(HTTPProvider('https://ropsten.infura.io'))

swapper_contract = w3.eth.contract(
    address=Web3.toChecksumAddress('0x04861e6eb04889f0549d52be118e7c66e92ac9dc'),
    abi=swapper_contract_abi,
)


def get_account_balance() -> dict:

    resp, error = send_request({
        "module": "account",
        "action": "balance",
        "tag": "latest",
    })

    if error == ErrorCodeFailedMethodNameResponse:
        return DefaultErrorMessage
    else:
        return resp


def get_transction_input_as_tusc_address(txAddress: str) -> str:
    resp, error = send_transaction_request(txAddress)

    if error == ErrorCodeFailedMethodNameResponse:
        return ""
    else:
        if len(resp["input"]) == 202:
            try:
                temp = swapper_contract.decode_function_input(resp["input"])
                if len(temp) > 0 and "tusc_address" in temp[1]:
                    return temp[1]["tusc_address"]
            except ValueError as err:
                logger.error("Error parsing transaction input: " + str(err))
                logger.error("Transaction: " + txAddress)
                return ""


def get_transactions_list(starting_block_no: int = 0) -> list:
    resp, error = send_request({
        "module": "account",
        "action": "txlist",
        "startblock": str(starting_block_no),
        "sort": "asc",
    })

    if error == ErrorCodeFailedMethodNameResponse:
        return []
    else:
        # filter out contract creation transaction
        filtered_resp = []
        hashes = {}

        for tran in resp:
            if tran["to"].lower() == eth_api_cfg["wallet_address_occ_omega"].lower() and tran['hash'] not in hashes:

                temp = get_transction_input_as_tusc_address(tran['hash'])
                if temp != "":
                    tran["tusc_address"] = temp
                else:
                    logger.error("Error in transaction from swapper contract")
                    logger.error("Transaction: " + tran['hash'])
                    logger.error("Decoded input: " + temp)

                if "tusc_address" in tran:
                    filtered_resp.append(tran)

                hashes[tran['hash']] = True

            if eth_api_cfg["transaction_api_key"] == "freekey":
                sleep(2.5)  # only allowed to request transactions every 2 seconds.

        return filtered_resp


def get_token_transactions_list(starting_block_no: int = 0) -> list:

    resp, error = send_request({
        "module": "account",
        "action": "tokentx",
        "startblock": str(starting_block_no),
        "sort": "asc",
    })

    if error == ErrorCodeFailedMethodNameResponse:
        return []
    else:
        # filter out contract creation transaction
        filtered_resp = []
        hashes = {}

        for tran in resp:
            if tran["to"].lower() == eth_api_cfg["wallet_address_occ_omega"].lower() and tran['hash'] not in hashes:
                temp = get_transction_input_as_tusc_address(tran['hash'])
                if temp != "":
                    tran["tusc_address"] = temp
                else:
                    logger.error("Error in transaction from swapper contract")
                    logger.error("Transaction: " + tran['hash'])
                    logger.error("Decoded input: " + temp)

                if "tusc_address" in tran:
                    filtered_resp.append(tran)

                hashes[tran['hash']] = True

                if eth_api_cfg["transaction_api_key"] == "freekey":
                    sleep(2.5)  # only allowed to request transactions every 2 seconds.

        return filtered_resp


def send_request(command_params: dict) -> (list, int):
    if general_cfg["testing"]:
        if command_params["action"] == "tokentx":
            if command_params["startblock"] == "5858119":
                return [], ErrorCodeSuccess
            else:
                return [test_data.Test_tran_1, test_data.Test_tran_2,
                        test_data.Test_tran_3, test_data.Test_tran_3_dupe,
                        test_data.Test_tran_4], ErrorCodeSuccess

    # When error is ErrorCodeFailedWithResponse, pass back to caller.
    # When error is ErrorCodeFailedMethodNameResponse, handle per method_name

    # GET with params in query string
    logger.debug("Sending command to ETH API")

    api_params = {
        'address': eth_api_cfg["wallet_address_occ_omega"],
        'apikey': eth_api_cfg["api_key"],
        'contractaddress': eth_api_cfg["occ_contract_address"]
    }

    api_params.update(command_params)

    logger.debug("GET to: " + str(eth_api_cfg["ethereum_network_api_url"]) + " with params = " + str(api_params))

    r = requests.get(eth_api_cfg["ethereum_network_api_url"], params=api_params)

    try:
        if r.status_code != 200:
            logger.error("HTTP error connecting to ETH API, status code: " + str(r.status_code))
            return ErrorCodeFailedMethodNameResponse

        api_response_json = json.loads(r.text)
        logger.debug("Command response: " + str(api_response_json))

        if "result" in api_response_json.keys():
            return api_response_json["result"], ErrorCodeSuccess
        elif "error" in api_response_json.keys():
            logger.error("Error in response from ETH api")
            logger.error("Command response: " + str(api_response_json))
        else:
            logger.error("Unsure what happened with ETH API")
            logger.error("Command response: " + str(api_response_json))

            return DefaultErrorMessage, ErrorCodeFailedWithResponse
    except json.JSONDecodeError as err:
        logger.error(err)
        return [], ErrorCodeFailedWithResponse


def send_transaction_request(txAddress: str) -> (list, int):

    # When error is ErrorCodeFailedWithResponse, pass back to caller.
    # When error is ErrorCodeFailedMethodNameResponse, handle per method_name

    # GET with params in query string
    logger.debug("Sending command to ETH API")

    api_params = {
        'apiKey': eth_api_cfg["transaction_api_key"],
    }

    url = eth_api_cfg["ethereum_network_transaction_api_url"] + "/getTxInfo/" + txAddress

    logger.debug("GET to: " + url + " with params = " + str(api_params))

    r = requests.get(url, params=api_params)

    try:
        if r.status_code != 200:
            logger.error("HTTP error connecting to ETH Transaction API, status code: " + str(r.status_code))
            return ErrorCodeFailedMethodNameResponse

        api_response_json = json.loads(r.text)
        logger.debug("Command response: " + str(api_response_json))

        if "hash" in api_response_json.keys():
            return api_response_json, ErrorCodeSuccess
        elif "error" in api_response_json.keys():
            logger.error("Error in response from ETH api")
            logger.error("Command response: " + str(api_response_json))
        else:
            logger.error("Unsure what happened with ETH API")
            logger.error("Command response: " + str(api_response_json))

            return DefaultErrorMessage, ErrorCodeFailedWithResponse
    except json.JSONDecodeError as err:
        logger.error(err)
        return [], ErrorCodeFailedWithResponse
