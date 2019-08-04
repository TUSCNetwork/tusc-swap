from bottle import request, Bottle, response
from tusc_api import gate_tusc_api
import logging
import db_access.db as db
from datetime import datetime
from functools import wraps
logger = logging.getLogger('root')
logger.debug('loading')

tusc_web_ctrl = Bottle()


def log_to_logger(fn):
    """
    Wrap a Bottle request so that a log line is emitted after it's handled.
    (This decorator can be extended to take the desired logger as a param.)
    """
    @wraps(fn)
    def _log_to_logger(*args, **kwargs):
        request_time = datetime.now()
        actual_response = fn(*args, **kwargs)
        # modify this to log exactly what you need:
        logger.info('%s %s %s %s %s' % (request.remote_addr,
                                        request_time,
                                        request.method,
                                        request.url,
                                        response.status))
        return actual_response
    return _log_to_logger


tusc_web_ctrl.install(log_to_logger)

# example response
# ```
# {
#     "brain_priv_key": "WADING OLITORY LOBULAR MULLET EXSHIP SUTLERY CONSUTE STATE
#     MOOT CHEAP NEBULE FACIA CASHEL CYSTID LUNGY UVEAL",
#     "wif_priv_key": "5KCSDw3Dng58VNeKm3Xf8dpxwxxDpTxSAs4n5kdF6VzQZdDuUc3",
#     "pub_key": "TUSC6YZ8dWrEzGDnZPaRCxgXQ8yXeYMV9dvuUsrRskXW6FqTwPWyLT"
# }
# ```
@tusc_web_ctrl.route('/tusc/wallet/api/suggest_brain_key', method='GET')
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
@tusc_web_ctrl.route('/tusc/wallet/api/list_account_balances/<account_name>', method='GET')
def list_account_balances(account_name):
    logger.debug('list_account_balances')
    return gate_tusc_api.list_account_balances(account_name)


# Accepted fields: account_name (str), public_key (str)
@tusc_web_ctrl.route('/tusc/wallet/api/register_account', method='POST')
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

# example response
# {
#     "occ_swapped": "102348857281025782841613573730",
#     "tusc_swapped": "5117442864051290"
# }
# Note that OCC uses 18 decimal places of precision and TUSC uses 5. So the above values are really:
# OCC: 102348857281.025782841613573730
# TUSC: 51174428640.51290
@tusc_web_ctrl.route('/tusc/swapper/api/swap_stats', method='GET')
def swap_stats():
    logger.debug('swap_stats')
    return db.get_swap_stats()


tusc_web_ctrl.run()

logger.debug('loaded')
