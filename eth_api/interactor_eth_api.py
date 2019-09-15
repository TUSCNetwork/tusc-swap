import eth_api.gate_eth as gate
import db_access.db as db
import logging
import tusc_api.gate_tusc_api
from config import cfg

logger = logging.getLogger('root')
logger.debug('loading')

general_cfg = cfg["general"]


def get_account_balance() -> dict:
    return gate.get_account_balance()


def get_transction_input_as_tusc_address(txAddress: str) -> str:
    return gate.get_transction_input_as_tusc_address(txAddress)


def get_transactions_list(starting_block_no: int = 0) -> list:
    return gate.get_transactions_list(starting_block_no)


def get_token_transactions_list(starting_block_no: int = 0) -> list:
    return gate.get_token_transactions_list(starting_block_no)


def handle_new_transactions():
    # Loop through transactions list and find all hashes.
    highest_block = db.get_highest_block_handled()
    initial_highest_block = highest_block
    transactions = get_token_transactions_list(highest_block)

    if len(transactions) == 0:
        return

    transaction_hashes = []

    for i in range(len(transactions)):
        if all(k not in transactions[i] for k in ('hash', 'input', 'blockNumber', 'value', 'tusc_address')):
            logger.error("Could not find one of the needed fields 'hash', 'input', 'blockNumber'"
                         ", 'tusc_address' or 'value' in transaction: " + str(transactions[i]))
        else:
            # build a list of transaction hashes to check against the db
            transaction_hashes.append(transactions[i]['hash'])

    transactions_already_performed = db.get_completed_transfers_by_hash_ids(transaction_hashes)

    for i in range(len(transactions)):
        if transactions[i]['hash'] not in transactions_already_performed:
            # New transaction, perform transfer
            success = perform_transfer(transactions[i])

            if success:
                if int(transactions[i]['blockNumber']) > highest_block:
                    highest_block = int(transactions[i]['blockNumber'])

    if highest_block > initial_highest_block:
        db.set_highest_block_handled(highest_block)


def perform_transfer(transaction: dict) -> bool:
    # Ensure TUSC account exists
    does_account_exist = tusc_api.gate_tusc_api.get_account(transaction["tusc_address"])

    if 'error' in does_account_exist:
        logger.error("Attempting to transfer for transaction " +
                      transaction["hash"] + " but TUSC account " + transaction["tusc_address"] +
                      " does not exist. Error returned from get_account: " + str(does_account_exist))
        return False

    logger.debug("Preparing transfer for " + transaction["hash"])

    # Transfer rate is 2 OCC to 1 TUSC
    # TODO: calculate transfer amount then perform the transfer

    occ_amount = int(transaction["value"])
    # OCC uses 18 decimal places. So 10,000,000,000,000,000,000,000 = 10,000
    # TUSC uses 5 decimal places. So 1,000,000,000 = 10,000
    # Take OCC amount, divide by 2 to get TUSC amount, reduce precision to 5 decimal places
    tusc_amount = round((occ_amount/2) / 1000000000000000000)
    logger.debug("Transferring " + str(occ_amount) + " OCC to " + str(tusc_amount) +
                  " TUSC into TUSC account " + transaction["tusc_address"] + " for transaction " + transaction["hash"])

    # The wallet accepts TUSC amount at precision. Meaning if you give it 100, you're actually transferring 100 TUSC.
    resp = tusc_api.gate_tusc_api.transfer(transaction["tusc_address"], str(tusc_amount))
    if 'error' in resp:
        logger.error("Transfer for transaction " + transaction["hash"] + " failed!")
        return False

    db.save_completed_transfer(transaction["hash"], transaction["tusc_address"], occ_amount, tusc_amount)

    return True


def perform_all_recovery_transactions():
    transactions = db.get_recovery_list()

    if len(transactions) == 0:
        return

    transaction_hashes = []

    for i in range(len(transactions)):
        # build a list of transaction hashes to check against the db
        transaction_hashes.append(transactions[i]['eth_transaction_hash'])

    transactions_already_performed = db.get_completed_transfers_by_hash_ids(transaction_hashes)

    for i in range(len(transactions)):
        transaction = transactions[i]
        if transaction['eth_transaction_hash'] not in transactions_already_performed:
            if not transaction['swap_performed']:
                # Ensure TUSC account exists
                does_account_exist = tusc_api.gate_tusc_api.get_account(transaction["tusc_account_name"])

                if 'error' in does_account_exist:
                    logger.error("Attempting to transfer for transaction " +
                                 transaction["eth_transaction_hash"] + " but TUSC account " + transaction["tusc_account_name"] +
                                 " does not exist. Error returned from get_account: " + str(does_account_exist))
                    return False

                logger.debug("Preparing transfer for " + transaction["eth_transaction_hash"])
                logger.debug("Transferring " + str(transaction["occ_amount"]) + " OCC to " + str(transaction["tusc_amount"]) +
                             " TUSC into TUSC account " + transaction["tusc_account_name"] + " for transaction " + transaction[
                                 "eth_transaction_hash"])

                resp = tusc_api.gate_tusc_api.transfer(transaction["tusc_account_name"], str(transaction["tusc_amount"]))
                if 'error' in resp:
                    logger.error("Transfer for transaction " + transaction["eth_transaction_hash"] + " failed!")
                    return False

                db.update_recovery_swap_performed(transaction)
                db.save_completed_transfer(transaction["eth_transaction_hash"],
                                           transaction["tusc_account_name"],
                                           transaction["occ_amount"],
                                           transaction["tusc_amount"])
        else:
            logger.debug("Skipping recovery for transaction " + transaction["eth_transaction_hash"] +
                         ". Already handled.")

    db.set_highest_block_handled(general_cfg['highest_block_number_handled'])

