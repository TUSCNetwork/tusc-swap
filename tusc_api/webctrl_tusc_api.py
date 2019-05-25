from bottle import route, request
import logging
from tusc_api import gate_tusc_api
from time import sleep

logger = logging.getLogger('root')
logger.debug('loading')

# example response
# ```
# {
#     "brain_priv_key": "WADING OLITORY LOBULAR MULLET EXSHIP SUTLERY CONSUTE STATE
#     MOOT CHEAP NEBULE FACIA CASHEL CYSTID LUNGY UVEAL",
#     "wif_priv_key": "5KCSDw3Dng58VNeKm3Xf8dpxwxxDpTxSAs4n5kdF6VzQZdDuUc3",
#     "pub_key": "TUSC6YZ8dWrEzGDnZPaRCxgXQ8yXeYMV9dvuUsrRskXW6FqTwPWyLT"
# }
# ```
@route('/tusc/wallet/api/suggest_brain_key/<sleep_time:int>', method='GET')
def suggest_brain_key(sleep_time: int):
    logger.debug('suggest_brain_key')
    sleep(sleep_time)
    return gate_tusc_api.suggest_brain_key()


# example response
# [
#   {
#       "amount": "999494821504412",
#       "asset_id": "1.3.0"
#   },
#   ...
# ]
@route('/tusc/wallet/api/list_account_balances/<account_name>', method='GET')
def list_account_balances(account_name):
    logger.debug('list_account_balances')
    return gate_tusc_api.list_account_balances(account_name)


# Accepted fields: account_name (str), public_key (str)
@route('/tusc/wallet/api/register_account', method='POST')
def register_account():
    data = request.json
    logger.debug('register_account')

    account_name = ""
    if "account_name" in data:
        account_name = data["account_name"]

    public_key = ""
    if "public_key" in data:
        public_key = data["public_key"]

    if account_name != "" and public_key != "":
        return gate_tusc_api.register_account(account_name, public_key)
    else:
        return


logger.debug('loaded')
