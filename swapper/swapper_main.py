

import log

logger = log.setup_custom_logger('root')
logger.debug('Starting OCC to TUSC swapper')

import eth_api.interactor_eth_api as eth_api
import db_access.db as db

if __name__ == '__main__':
    logger.debug('Starting swapper')
    #print(eth_api.handle_new_transactions())
    db.initiate_database_connection()

    print("Highest block handled = {}".format(db.get_highest_block_handled()))
