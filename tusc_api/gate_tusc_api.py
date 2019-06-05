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

tusc_api_cfg = cfg["tusc_api"]


def build_request_dict(method_name: str, params: list) -> dict:
    tusc_wallet_command_structure = {
        "jsonrpc": tusc_api_cfg["tusc_wallet_rpc_version"],
        "method": method_name,
        "params": params,
        "id": 1
    }
    return tusc_wallet_command_structure


def get_tusc_url() -> str:
    return "http://" + \
           tusc_api_cfg["tusc_wallet_ip"] + ":" + \
           tusc_api_cfg["tusc_wallet_port"] + \
           tusc_api_cfg["tusc_wallet_rpc_endpoint"]


def suggest_brain_key() -> dict:
    resp, error = send_request("suggest_brain_key", [], True)

    if error == ErrorCodeFailedMethodNameResponse:
        # handle suggest_brain_key specific errors
        return DefaultErrorMessage
    else:
        return resp


def list_account_balances(account_name: str) -> dict:
    resp, error =  send_request("list_account_balances", [account_name])

    if error == ErrorCodeFailedMethodNameResponse:
        # handle list_account_balances specific errors
        if "data" in resp["error"].keys():
            if "stack" in resp["error"]["data"].keys():
                for stack_obj in resp["error"]["data"]["stack"]:
                    if "format" in stack_obj:
                        if "rec && rec->name" in stack_obj["format"]:
                            return {"error": "Account name '" + account_name + "' could not be found. "}

        return DefaultErrorMessage
    else:
        return resp


def register_account(account_name: str, public_key: str) -> dict:
    # register_account <account_name> <owner-public_key> <active-public_key> <registrar_account>
    # <referrer_account> <referrer_percent> <broadcast>
    account_name_restrictions = "Account names must be more than 7 and less than 64 characters. " \
                                "They must consist of lower case characters, numbers, and '-'. " \
                                "They Cannot start with a number."
    if len(account_name) < 8:
        return {"error": "Account name '" + account_name + "' is too short. " + account_name_restrictions}
    if len(account_name) > 63:
        return {"error": "Account name '" + account_name + "' is too long. " + account_name_restrictions}

    resp, error = send_request("register_account",
                               [account_name,
                                public_key,
                                public_key,
                                tusc_api_cfg["swap_account_name"],
                                tusc_api_cfg["swap_account_name"],
                                75,
                                True], False)

    if error == ErrorCodeFailedMethodNameResponse:
        if "data" in resp["error"].keys():
            if "stack" in resp["error"]["data"].keys():
                for stack_obj in resp["error"]["data"]["stack"]:
                    if "format" in stack_obj:
                        if "rec && rec->name" in stack_obj["format"]:
                            return {"error": "Account name '" + account_name + "' already in use. "
                                                                               "Please use a different account name."}

                        if "is_valid_name(name" in stack_obj["format"]:
                            logger.error("Account name already exists")
                            return {"error": "Account name '" + account_name + "' is invalid. " +
                                             account_name_restrictions}
        return DefaultErrorMessage
    else:
        return resp


def suggest_brain_key() -> dict:
    resp, error = send_request("suggest_brain_key", [], True)

    if error == ErrorCodeFailedMethodNameResponse:
        # handle suggest_brain_key specific errors
        return DefaultErrorMessage
    else:
        return resp


def get_account(account_name: str) -> dict:
    resp, error = send_request("get_account", [account_name], True)

    if error == ErrorCodeFailedMethodNameResponse:
        return DefaultErrorMessage
    else:
        return resp


def transfer(to: str, amount: str) -> dict:
    resp, error = send_request("transfer",
                               [tusc_api_cfg["swap_account_name"],
                                to,
                                amount,
                                "TUSC",
                                "",
                                True], False)

    if error == ErrorCodeFailedMethodNameResponse:
        return DefaultErrorMessage
    else:
        return resp


def send_request(method_name: str, params: list, do_not_log_data=False) -> (dict, int):
    # when error is ErrorCodeFailedWithResponse, pass back to caller.
    # When error is ErrorCodeFailedMethodNameResponse, handle per method_name
    req = build_request_dict(method_name, params)

    # POST with JSON
    command_json = json.dumps(req)
    logger.debug("Sending command to TUSC wallet")

    if do_not_log_data is False:
        logger.debug("Command payload: " + str(command_json))

    url = get_tusc_url()

    logger.debug("posting to: " + str(url))

    r = requests.post(url, data=command_json)

    try:
        api_response_json = json.loads(r.text)

        if "result" in api_response_json.keys():
            if do_not_log_data is False:
                logger.debug("Command response: " + str(api_response_json))
            return {"result": api_response_json["result"]}, ErrorCodeSuccess
        elif "error" in api_response_json.keys():
            logger.error("Error in response from TUSC api")
            logger.error("Command response: " + str(api_response_json))
            generic_errors_handled, error = handle_generic_tusc_errors(api_response_json)
            if error == 1:
                return generic_errors_handled, ErrorCodeFailedWithResponse
            else:
                return generic_errors_handled, ErrorCodeFailedMethodNameResponse
        else:
            logger.error("Unsure what happened with TUSC API")
            logger.error("Command response: " + str(api_response_json))

            return DefaultErrorMessage, ErrorCodeFailedWithResponse
    except json.JSONDecodeError as err:
        logger.error(err)
        return {"error": "Internal server error"}, ErrorCodeFailedWithResponse


def handle_generic_tusc_errors(api_response_json: dict) -> (dict, int):
    if "data" in api_response_json["error"].keys():
        if "stack" in api_response_json["error"]["data"].keys():
            for stack_obj in api_response_json["error"]["data"]["stack"]:
                if "format" in stack_obj:

                    # Wallet is locked
                    if "is_locked" in stack_obj["format"]:
                        logger.error("Cannot perform operation, TUSC Wallet is locked")
                        return DefaultErrorMessage, ErrorCodeFailedWithResponse

    return api_response_json, ErrorCodeFailedMethodNameResponse


logger.debug('loaded')
