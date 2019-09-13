from flask import Blueprint, request

import requests
from tusc_api import gate_tusc_api
import logging
import db_access.db as db
import json
from config import cfg
from datetime import datetime, timedelta

logger = logging.getLogger('root')
logger.debug('loading')

tusc_api = Blueprint('tusc_api', 'tusc_api', url_prefix='')
general_cfg = cfg["general"]

ip_addresses = {}

# example response
# ```
# {
#     "brain_priv_key": "WADING OLITORY LOBULAR MULLET EXSHIP SUTLERY CONSUTE STATE
#     MOOT CHEAP NEBULE FACIA CASHEL CYSTID LUNGY UVEAL",
#     "wif_priv_key": "5KCSDw3Dng58VNeKm3Xf8dpxwxxDpTxSAs4n5kdF6VzQZdDuUc3",
#     "pub_key": "TUSC6YZ8dWrEzGDnZPaRCxgXQ8yXeYMV9dvuUsrRskXW6FqTwPWyLT"
# }
# ```
@tusc_api.route('/wallet/suggest_brain_key', methods=["GET"])
def suggest_brain_key():
    logger.debug('suggest_brain_key')
    return gate_tusc_api.suggest_brain_key()


# example response
# [
#   {
#       "amount": "999494821504412",
#       "asset_id": "1.3.0"
#   },
#   ...
# ]
@tusc_api.route('/wallet/list_account_balances/<account_name>', methods=["GET"])
def list_account_balances(account_name):
    logger.debug('list_account_balances')
    return gate_tusc_api.list_account_balances(account_name)


# Accepted fields: account_name (str), public_key (str)
@tusc_api.route('/wallet/register_account', methods=["POST"])
def register_account():
    global ip_addresses
    logger.debug('register_account')
    content = request.json
    ip_address = request.remote_addr

    if not is_ip_allowed(ip_address):
        return {"error": "For security purposes, you are only allowed to register an account every " +
                         str(general_cfg['ip_request_blocking_hours']) + " hours."}

    did_recaptcha_succeed = False
    if 'recaptcha_response' in content:
        did_recaptcha_succeed = handle_captcha(content['recaptcha_response'], ip_address)

    if not did_recaptcha_succeed:
        return {"error": "Failed reCAPTCHA validation"}

    if 'account_name' in content and 'public_key' in content:
        res = gate_tusc_api.register_account(content['account_name'], content['public_key'])

        if 'error' not in res:
            now = datetime.now()
            ip_addresses[ip_address] = now

        return res
    else:
        return {"error": "Expected account_name and public_key in json string"}


def is_ip_allowed(ip_address) -> bool:
    global ip_addresses

    now = datetime.now()
    if ip_address in ip_addresses:
        if ip_addresses[ip_address] > now - timedelta(hours=general_cfg['ip_request_blocking_hours']):
            return False
        else:
            return True

    return True


def handle_captcha(captcha_response, ip) -> bool:
    try:
        content = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': general_cfg['captcha_secret'],
                'response': captcha_response,
                'remoteip': ip,
            }
        ).content
    except ConnectionError:
        return False

    content = json.loads(content)

    if not 'success' in content or not content['success']:
        return False
    else:
        return True

# example response
# {
#     "end_of_swap_date": "2019-10-01 00:00:00",
#     "occ_left_to_swap": "100000000000000000000000000000",
#     "occ_swapped": "0",
#     "tusc_swapped": "0"
# }
# Note that OCC uses 18 decimal places of precision and TUSC uses 5. So the above values are really:
# OCC: 102348857281.025782841613573730
# TUSC: 51174428640.51290
@tusc_api.route('/db/swap_stats', methods=["GET"])
def swap_stats():
    return db.get_swap_stats()

logger.debug('loaded')
