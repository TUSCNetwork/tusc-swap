

import log

logger = log.setup_custom_logger('root')
logger.debug('Starting OCC to TUSC swapper')

import eth_api.interactor_eth_api as eth_api
import db_access.db as db

if __name__ == '__main__':
    logger.debug('Starting swapper')
    db.initiate_database_connection()

    print(db.get_swap_stats())
