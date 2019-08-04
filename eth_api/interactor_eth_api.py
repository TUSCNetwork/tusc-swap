import eth_api.gate_eth as gate
import db_access.db as db
import logging
import tusc_api.gate_tusc_api

logger = logging.getLogger('root')
logger.debug('loading')


def get_account_balance() -> dict:
    return gate.get_account_balance()


def get_transactions_list(starting_block_no: int = 0) -> list:
    return gate.get_transactions_list(starting_block_no)


def get_token_transactions_list(starting_block_no: int = 0) -> list:
    return gate.get_token_transactions_list(starting_block_no)


def handle_new_transactions():
    # Loop through transactions list and find all hashes.
    highest_block = db.get_highest_block_handled()
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

    db.set_highest_block_handled(highest_block)


def perform_transfer(transaction: dict) -> bool:
    # Ensure TUSC account exists
    does_account_exist = tusc_api.gate_tusc_api.get_account(transaction["tusc_address"])

    if 'error' in does_account_exist:
        logging.error("Attempting to transfer for transaction " +
                      transaction["hash"] + " but TUSC account " + transaction["tusc_address"] +
                      " does not exist. Error returned from get_account: " + str(does_account_exist))
        return False

    logging.debug("Preparing transfer for " + transaction["hash"])

    # Transfer rate is 2 OCC to 1 TUSC
    # TODO: calculate transfer amount then perform the transfer

    occ_amount = int(transaction["value"])
    # OCC uses 18 decimal places. So 10,000,000,000,000,000,000,000 = 10,000
    # TUSC uses 5 decimal places. So 1,000,000
    # Take OCC amount, divide by 2 to get TUSC amount, reduce precision to 5 decimal places
    tusc_amount = round((occ_amount/2) / 10000000000000)
    logging.debug("Transferring " + str(occ_amount) + " OCC to " + str(tusc_amount) +
                  " TUSC into TUSC account " + transaction["tusc_address"] + " for transaction " + transaction["hash"])

    resp = tusc_api.gate_tusc_api.transfer(transaction["tusc_address"], str(tusc_amount))
    if 'error' in resp:
        logging.error("Transfer for transaction " + transaction["hash"] + " failed!")
        return False

    db.save_completed_transfer(transaction, transaction["tusc_address"], occ_amount, tusc_amount)

    return True
