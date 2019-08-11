import logging
import psycopg2
import psycopg2.extras
from decimal import Decimal
from datetime import datetime
from config import cfg

logger = logging.getLogger('root')
logger.debug('loading')

db_cfg = cfg["db"]
general_cfg = cfg["general"]

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
    try:
        cur.execute("""select max(block_number) as highest_block_handled from highest_blocks_handled""")
    except:
        logger.exception('Failed get_highest_block_handled')
        return 0

    rows = cur.fetchall()
    if len(rows) < 1:
        return 0

    if rows[0]['highest_block_handled'] is None:
        return 0

    return int(rows[0]['highest_block_handled'])


def set_highest_block_handled(block_number: int):
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("insert into highest_blocks_handled "
                "(block_number) values ({});".format(block_number))
        conn.commit()
    except:
        logger.exception('Failed set_highest_block_handled')
        return

    return


def get_completed_transfers_by_hash_ids(transaction_hashes: list) -> dict:
    # Query DB and fill a dict with all the hashes
    if len(transaction_hashes) < 1 or transaction_hashes is None:
        return {}

    hashes_with_quotes = ["'" + hash + "'" for hash in transaction_hashes]
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("""select * from transfers where 
        eth_transaction_hash in ({}) """.format(','.join(hashes_with_quotes)))
    except:
        logger.exception('Failed get_completed_transfers_by_hash_ids')
        return {}

    rows = cur.fetchall()
    if len(rows) < 1:
        return {}

    return {i['eth_transaction_hash']: i for i in rows}


def save_completed_transfer(transaction: dict,
                            tusc_account_name: str,
                            amount_in_occ_transferred: int,
                            amount_in_tusc_transferred: int):

    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    q = "insert into transfers (eth_transaction_hash, tusc_account_name, occ_amount, tusc_amount) " \
        "values ('{}','{}', '{}', '{}');".\
        format(transaction['hash'], tusc_account_name, amount_in_occ_transferred, amount_in_tusc_transferred)

    try:
        cur.execute(q)
        conn.commit()
    except:
        logger.exception('Failed save_completed_transfer: transaction = ' + str(transaction) +
                         ', tusc_account_name = ' + tusc_account_name + ', amount_in_occ_transferred = ' +
                         str(amount_in_occ_transferred) + ", amount_in_tusc_transferred = " +
                         str(amount_in_tusc_transferred))
        return

    return


def get_swap_stats() -> dict:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("select sum(CAST(occ_amount AS NUMERIC)) as occ_swapped, "
                    "sum(CAST(tusc_amount AS NUMERIC)) as tusc_swapped from transfers")
    except:
        logger.exception('Failed to get swap stats')
        return {}

    rows = cur.fetchall()

    occ_swapped = 0
    tusc_swapped = 0

    seconds_to_end_of_swap = datetime.strptime(general_cfg["shut_off_date"], '%Y-%m-%d %H:%M:%S') - datetime.now()

    if len(rows) < 1:
        return {"occ_swapped": str(occ_swapped),
                "tusc_swapped": str(tusc_swapped),
                "occ_left_to_swap": format(Decimal(general_cfg["maximum_occ"]), 'f'),
                "seconds_to_end_of_swap": str(seconds_to_end_of_swap.total_seconds())
                }

    if rows[0]["occ_swapped"] is not None:
        occ_swapped = rows[0]["occ_swapped"]

    if rows[0]["tusc_swapped"] is not None:
        tusc_swapped = rows[0]["tusc_swapped"]

    occ_left_to_swap = Decimal(general_cfg["maximum_occ"]) - occ_swapped

    return {
        "occ_swapped": str(occ_swapped),
        "tusc_swapped": str(tusc_swapped),
        "occ_left_to_swap": format(occ_left_to_swap, 'f'),
        "seconds_to_end_of_swap": str(seconds_to_end_of_swap.total_seconds())
    }


logger.debug('loaded')
