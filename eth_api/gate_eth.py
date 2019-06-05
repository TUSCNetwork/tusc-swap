import requests
import json
import logging
from config import cfg

logger = logging.getLogger('root')
logger.debug('loading')

DefaultErrorMessage = {"error": "Something went wrong, please contact tusc support"}

ErrorCodeSuccess = 0
ErrorCodeFailedWithResponse = 1
ErrorCodeFailedMethodNameResponse = 2

eth_api_cfg = cfg["eth_api"]


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
        return resp


def send_request(command_params: dict) -> (dict, int):
    # When error is ErrorCodeFailedWithResponse, pass back to caller.
    # When error is ErrorCodeFailedMethodNameResponse, handle per method_name

    # GET with params in query string
    logger.debug("Sending command to ETH API")

    api_params = {
        'address': eth_api_cfg["wallet_address_occ_omega"],
        'apikey': eth_api_cfg["api_key"],
    }

    api_params.update(command_params)

    logger.debug("GET to: " + str(eth_api_cfg["ethereum_network_api_url"]) + " with params = " + str(api_params))

    r = requests.get(eth_api_cfg["ethereum_network_api_url"], params=api_params)

    try:
        api_response_json = json.loads(r.text)
        logger.debug("Command response: " + str(api_response_json))

        if "result" in api_response_json.keys():
            return api_response_json["result"], ErrorCodeSuccess
        elif "error" in api_response_json.keys():
            logger.error("Error in response from ETH api")
            logger.error("Command response: " + str(api_response_json))
            # generic_errors_handled, error = handle_generic_tusc_errors(api_response_json)
            # if error == 1:
            #     return generic_errors_handled, ErrorCodeFailedWithResponse
            # else:
            #     return generic_errors_handled, ErrorCodeFailedMethodNameResponse
        else:
            logger.error("Unsure what happened with ETH API")
            logger.error("Command response: " + str(api_response_json))

            return DefaultErrorMessage, ErrorCodeFailedWithResponse
    except json.JSONDecodeError as err:
        logger.error(err)
        return {"error": "Internal server error"}, ErrorCodeFailedWithResponse
