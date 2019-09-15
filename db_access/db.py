import logging
import psycopg2
import psycopg2.extras
import psycopg2.errors
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


def get_all_transfers_by_hash_ids(transaction_hashes: list) -> dict:
    # Query DB and fill a dict with all the hashes
    if len(transaction_hashes) < 1 or transaction_hashes is None:
        return {}

    hashes_with_quotes = ["'" + hash + "'" for hash in transaction_hashes]
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("""select * from transfers where 
        eth_transaction_hash in ({})""".format(','.join(hashes_with_quotes)))
    except:
        logger.exception('Failed get_all_transfers_by_hash_ids')
        return {}

    rows = cur.fetchall()
    if len(rows) < 1:
        return {}

    return {i['eth_transaction_hash']: i for i in rows}


def get_failed_transfers() -> dict:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("""select * from transfers where success = false;""")
    except:
        logger.exception('Failed get_failed_transfers')
        return {}

    rows = cur.fetchall()
    if len(rows) < 1:
        return {}

    return rows


def save_transfer(transaction_hash: str,
                  tusc_account_name: str,
                  amount_in_occ_transferred: int,
                  amount_in_tusc_transferred: int,
                  success: bool):

    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    q = "insert into transfers (eth_transaction_hash, tusc_account_name, occ_amount, tusc_amount, success) " \
        "values ('{}','{}', '{}', '{}', {});".\
        format(transaction_hash,
               tusc_account_name.strip(),
               amount_in_occ_transferred,
               amount_in_tusc_transferred,
               success)

    try:
        cur.execute(q)
        conn.commit()
    except:
        logger.exception('Failed save_completed_transfer: transaction_hash = ' + transaction_hash +
                         ', tusc_account_name = ' + tusc_account_name.strip() + ', amount_in_occ_transferred = ' +
                         str(amount_in_occ_transferred) + ", amount_in_tusc_transferred = " +
                         str(amount_in_tusc_transferred))
        return

    return


def update_transfer(transaction_hash: str,
                    success: bool):

    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    q = "update transfers set success = {} where eth_transaction_hash = '{}'".\
        format(success, transaction_hash)

    try:
        cur.execute(q)
        conn.commit()
    except:
        logger.exception('Failed update_transfer: transaction_hash = ' + transaction_hash +
                         ', success = ' + str(success))
        return

    return


def save_completed_transfer(transaction_hash: str,
                            tusc_account_name: str,
                            amount_in_occ_transferred: int,
                            amount_in_tusc_transferred: int):
    save_transfer(transaction_hash,tusc_account_name, amount_in_occ_transferred, amount_in_tusc_transferred, True)


def save_failed_transfer(transaction_hash: str,
                         tusc_account_name: str,
                         amount_in_occ_transferred: int,
                         amount_in_tusc_transferred: int):
    save_transfer(transaction_hash, tusc_account_name, amount_in_occ_transferred, amount_in_tusc_transferred, False)


def get_account_registration_count() -> int:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("""select count(*) as reg_count from tusc_account_registrations""")
    except:
        logger.exception('Failed get_account_registration_count')
        return 0

    rows = cur.fetchall()
    if len(rows) < 1:
        return 0

    if rows[0]['reg_count'] is None:
        return 0

    return int(rows[0]['reg_count'])


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

    number_of_registrations = get_account_registration_count()

    if len(rows) < 1:
        return {"occ_swapped": str(occ_swapped),
                "tusc_swapped": str(tusc_swapped),
                "occ_left_to_swap": format(Decimal(general_cfg["maximum_occ"]), 'f'),
                "end_of_swap_date": str(general_cfg["shut_off_date"]),
                "number_of_registrations": str(number_of_registrations)
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
        "end_of_swap_date": str(general_cfg["shut_off_date"]),
        "number_of_registrations": str(number_of_registrations)
    }


def get_recovery_list() -> dict:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("select * from mainnet_recovery")
    except:
        logger.exception('Failed to get swap stats')
        return {}

    rows = cur.fetchall()
    return rows


def get_recovery_list_account_names() -> dict:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("select distinct tusc_account_name, tusc_public_key from "
                    "mainnet_recovery order by tusc_account_name asc;")
    except:
        logger.exception('Failed to get swap stats')
        return {}

    rows = cur.fetchall()
    return rows


def update_recovery_public_key(transaction: dict):
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("update mainnet_recovery set tusc_public_key = '" + transaction["tusc_public_key"]
                    + "' where eth_transaction_hash = '" + transaction["eth_transaction_hash"] + "'")
        conn.commit()
    except:
        logger.exception('Failed to update recovery transaction. eth_transaction_hash = ' +
                         transaction["eth_transaction_hash"])

    return


def update_recovery_swap_performed(transaction: dict):
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("update mainnet_recovery set swap_performed = TRUE where "
                    "eth_transaction_hash = '" + transaction["eth_transaction_hash"] + "'")
        conn.commit()
    except:
        logger.exception('Failed to update recovery transaction swap performed. eth_transaction_hash = ' +
                         transaction["eth_transaction_hash"])

    return


def save_completed_registration(tusc_account_name: str,
                                tusc_public_key: str,):
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("select * from tusc_account_registrations "
                    "where tusc_account_name='" + tusc_account_name + "';")
    except:
        logger.exception('Failed to get swap stats')
        return {}

    rows = cur.fetchall()
    if len(rows) < 1: # account registration does not exist
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        q = "insert into tusc_account_registrations (tusc_account_name, tusc_public_key) " \
            "values ('{}','{}');".\
            format(tusc_account_name, tusc_public_key)

        try:
            cur.execute(q)
            conn.commit()
        except:
            logger.exception('Failed save_completed_registration: tusc_account_name = ' + tusc_account_name +
                             ', tusc_public_key = ' + tusc_public_key)
            return

    return


logger.debug('loaded')
