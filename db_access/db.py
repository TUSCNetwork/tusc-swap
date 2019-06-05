import yaml
import logging
import psycopg2
import psycopg2.extras
from config import cfg

logger = logging.getLogger('root')
logger.debug('loading')

db_cfg = cfg["db"]

global_conn = None


def initiate_database_connection():
    get_database_connection()


def get_database_connection():
    global global_conn
    constring = "dbname='{}' user='{}' host='{}' password='{}'".format(
        db_cfg["database"], db_cfg["user"], db_cfg["host"], db_cfg["password"])

    if global_conn is None:
        try:
            global_conn = psycopg2.connect(constring)
            logger.debug('DB Connection established')
            return global_conn
        except:
            raise Exception("No DB connection could be established. Exiting")
    else:
        return global_conn


def get_highest_block_handled() -> int:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""select max(block_number) as highest_block_handled from highest_blocks_handled""")
    rows = cur.fetchall()
    if len(rows) < 1:
        return 0

    return rows[0]['highest_block_handled']


def set_highest_block_handled(block_number: int):
    # TODO: handle setting in db
    return


def get_completed_transfers_by_hash_ids(transaction_hashes: list) -> dict:
    # Query DB and fill a dict with all the hashes

    # TODO: handle
    return {
        "thisIsATranHash": {},
        "thisIsAlsoATranHash": {},
    }


def save_completed_transfer(transaction: dict,
                            tusc_account_name: str,
                            amount_in_occ_transferred: int,
                            amount_in_tusc_transferred: int):


    # TODO: handle
    return

logger.debug('loaded')
