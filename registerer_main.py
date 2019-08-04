# Entry point to program.
# Handles setting up logging, config, and starting various services (DB, ethereum, tusc...)
import bottle
import log

logger = log.setup_custom_logger('root', 'registerer')
logger.debug('Starting OCC to TUSC registration server')

from tusc_api.webctrl_tusc_api import tusc_web_ctrl
import db_access.db as db

main_bottle = bottle.Bottle()

if __name__ == '__main__':
    logger.debug('Starting server')
    db.initiate_database_connection()
    main_bottle.merge(tusc_web_ctrl)
    main_bottle.run(host='localhost', port=8080)

app = bottle.default_app()
