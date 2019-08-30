from flask import Blueprint, request


from tusc_api import gate_tusc_api
import logging
import db_access.db as db

logger = logging.getLogger('root')
logger.debug('loading')

tusc_api = Blueprint('tusc_api', 'tusc_api', url_prefix='')

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
    logger.debug('register_account')
    content = request.json

    if 'account_name' in content and 'public_key' in content:
        return gate_tusc_api.register_account(content['account_name'], content['public_key'])
    else:
        return {"error": "Expected account_name and public_key in json string"}

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
