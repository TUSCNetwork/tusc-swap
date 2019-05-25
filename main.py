# Entry point to program.
# Handles setting up logging, config, and starting various services (DB, ethereum, tusc...)
import bottle

import log

logger = log.setup_custom_logger('root')
logger.debug('Starting OCC to TUSC swap server')

# Only here to load the API. TODO: turn it into an object if we care
import tusc_api.webctrl_tusc_api

if __name__ == '__main__':
    logger.debug('Starting server')
    bottle.run(host='localhost', port=8080)


app = bottle.default_app()