import log
import time
import signal as sig
import tusc_api.gate_tusc_api

from config import cfg

logger = log.setup_custom_logger('root', 'swapper')
logger.debug('Starting OCC to TUSC swapper')

import eth_api.interactor_eth_api as eth_api
import db_access.db as db

general_cfg = cfg["general"]


def keyboard_interrupt_handler(signal, frame):
    print("KeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signal))
    exit(0)


sig.signal(sig.SIGINT, keyboard_interrupt_handler)

if __name__ == '__main__':
    logger.debug('Starting swapper')
    db.initiate_database_connection()

    logger.debug('Recovering')
    tusc_api.gate_tusc_api.register_all_recovery_accounts()
    eth_api.perform_all_recovery_transactions()
    logger.debug('Done recovering.')
