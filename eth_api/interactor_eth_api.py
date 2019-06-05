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


def handle_new_transactions():
    # Loop through transactions list and find all hashes.
    highest_block = db.get_highest_block_handled()
    transactions = get_transactions_list(highest_block)

    transaction_hashes = []

    for i in range(len(transactions)):
        if all(k not in transactions[i] for k in ('hash', 'input', 'blockNumber', 'value')):
            # build a list of transaction hashes to check against the db
            transaction_hashes.append(transactions[i]['hash'])
        else:
            logger.error("Could not find one of the needed fields 'hash', 'input', 'blockNumber'"
                         ", or 'value' in transaction: " + str(transactions[i]))

    transactions_already_performed = db.get_completed_transfers_by_hash_ids(transaction_hashes)

    for i in range(len(transactions)):
        if transactions[i]['hash'] not in transactions_already_performed:
            # New transaction, perform transfer
            success = perform_transfer(transactions[i])

            if success:
                if transactions[i]['blockNumber'] > highest_block:
                    highest_block = transactions[i]['blockNumber']

    db.set_highest_block_handled(highest_block)


def perform_transfer(transaction: dict) -> bool:
    # Get TUSC account name from inside transaction 'input' field somehow? Still need Dapp to understand this part
    # account_name = transaction["input"]
    account_name = "FAKEACCOUNTNAME"
    # Ensure TUSC account exists
    does_account_exist = tusc_api.gate_tusc_api.get_account(account_name)

    if 'error' in does_account_exist:
        logging.error("Attempting to transfer for transaction " +
                      transaction["hash"] + " but TUSC account " + account_name +
                      " does not exist. Error returned from get_account: " + str(does_account_exist))
        return False

    logging.debug("Preparing transfer for " + transaction["hash"])

    tusc_account_name = transaction["input"]
    # occ_amount = transaction["value"]
    occ_amount = '10000000000000000'

    # Transfer rate is 2 OCC to 1 TUSC
    # TODO: calculate transfer amount then perform the transfer
    # Don't forget that TUSC does not use decimal. Figure out correct calculation of OCC to TUSC without decimal.
    tusc_amount = round(int(occ_amount)/2)
    logging.debug("Transferring: " + occ_amount + " OCC to transfer for " + str(tusc_amount) +
                  " TUSC for transaction " + transaction["hash"])

    resp = tusc_api.gate_tusc_api.transfer(tusc_account_name, str(tusc_amount))
    if 'error' in resp:
        logging.error("Transfer for transaction " + transaction["hash"] + " failed!")
        return False

    db.save_completed_transfer(transaction, tusc_account_name, occ_amount, tusc_amount)

    return True
