import log
import time
import signal as sig

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
    logger.debug('Starting')
    txAddress = "0x6e842ecf68302fa62ef1f4af91e431090dd56cd7bd807b173f6be2a8bb48e404"
    print("Tusc address for transaction '" + txAddress + "' = '" +
          eth_api.get_transction_input_as_tusc_address(txAddress) + "'")

