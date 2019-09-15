import requests
import json
import logging
import db_access.db as db
from config import cfg
import eth_api.interactor_eth_api as eth_api

logger = logging.getLogger('root')
logger.debug('loading')

DefaultErrorMessage = {"error": "Something went wrong, please contact tusc support"}

ErrorCodeSuccess = 0
ErrorCodeFailedWithResponse = 1
ErrorCodeFailedMethodNameResponse = 2

tusc_api_cfg = cfg["tusc_api"]
general_cfg = cfg["general"]


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
    resp, error = send_request("list_account_balances", [account_name])

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


def does_account_exist(account_name: str) -> bool:
    resp = list_account_balances(account_name)

    if "error" in resp:
        return False
    else:
        return True


def register_account(account_name: str, public_key: str) -> dict:
    # register_account <account_name> <owner-public_key> <active-public_key> <registrar_account>
    # <referrer_account> <referrer_percent> <broadcast>
    account_name_restrictions = "Account names must be more than 7 and less than 64 characters. " \
                                "They must consist of lower case characters, numbers, and '-'. " \
                                "They cannot start with a number."
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

                        if "base58str.size() > prefix_len:" in stack_obj["format"]:
                            logger.error("Public key error")
                            return {"error": "The public key '" + public_key + "' is invalid. Please double check "
                                                                               "that it is correct and resubmit."}

        return DefaultErrorMessage
    else:
        db.save_completed_registration(account_name, public_key)
        return resp


def get_account(account_name: str) -> dict:
    resp, error = send_request("get_account", [account_name], True)

    if error == ErrorCodeFailedMethodNameResponse:
        return DefaultErrorMessage
    else:
        return resp


def get_account_public_key(account_name: str) -> str:
    resp, error = send_request("get_account", [account_name], True)

    if error == ErrorCodeFailedMethodNameResponse:
        return "ERROR"
    else:
        # find the account's public key and return that
        return resp["result"]["owner"]["key_auths"][0][0]


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
    if general_cfg["testing"]:
        if method_name == "get_account" or \
                method_name == "transfer":
            return {}, ErrorCodeSuccess
        if method_name == "list_account_balances":
            return {}, ErrorCodeSuccess
        if method_name == "register_account":
            return {"error": "already in use"}, ErrorCodeSuccess

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

    # TODO: Handle timeouts if wallet isn't online
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


def get_recovery_public_keys():
    # Loop through transactions in mainnet_recovery and find pubkeys.
    transactions = db.get_recovery_list()

    if len(transactions) == 0:
        return

    for i in range(len(transactions)):
        transactions[i]['tusc_public_key'] = get_account_public_key(transactions[i]['tusc_account_name'].strip())
        db.update_recovery_public_key(transactions[i])


def register_all_recovery_accounts():
    transactions = db.get_recovery_list_account_names()

    if len(transactions) == 0:
        return

    for i in range(len(transactions)):
        acc_name = transactions[i]['tusc_account_name'].strip()
        acc_pub_key = transactions[i]['tusc_public_key'].strip()
        if not does_account_exist(transactions[i]['tusc_account_name'].strip()):
            # most likely doesn't exist, so create it
            res = register_account(acc_name, acc_pub_key)
            if 'error' in res:
                if 'already in use' in res['error']:
                    return

                logger.error("Failed to register recovery account '" + acc_name
                             + "' with public key '" + acc_pub_key + "'")
                return
            else:
                logger.debug("Successfully registered recovery account '" + acc_name
                             + "' with public key '" + acc_pub_key + "'")
        else:
            logger.debug("Skipping registration of recovery account '" + acc_name
                         + "' with public key '" + acc_pub_key + "'")


logger.debug('loaded')
