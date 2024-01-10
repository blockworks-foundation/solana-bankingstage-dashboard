import postgres_connection
import json

import recent_blocks_database
import transaction_database
from collections import defaultdict


def find_transaction_details_by_sig(tx_sig: str):
    # transaction table primary key is used
    maprows = postgres_connection.query(
        """
        SELECT
            tx_slot_agg.transaction_id,
            tx_slot_agg.signature,
            tx_slot_agg.first_slot AS first_notification_slot,
            tx_slot_agg.min_utc_timestamp AS utc_timestamp,
            -- optional fields from transaction_infos
            txi.is_successful,
            txi.processed_slot,
            txi.cu_requested,
            txi.prioritization_fees
        FROM (
            SELECT
                signature,
                -- note: min() is arbitrary
                min(tx_slot.transaction_id) AS transaction_id,
                min(slot) AS first_slot, min(utc_timestamp) AS min_utc_timestamp
            FROM banking_stage_results_2.transaction_slot tx_slot
            INNER JOIN banking_stage_results_2.transactions txs ON txs.transaction_id=tx_slot.transaction_id
            LEFT JOIN banking_stage_results_2.transaction_infos txi ON txi.transaction_id=tx_slot.transaction_id
            WHERE txs.signature = %s
            GROUP BY signature
        ) as tx_slot_agg
        LEFT JOIN banking_stage_results_2.transaction_infos txi ON txi.transaction_id=tx_slot_agg.transaction_id
        """, args=[tx_sig])

    assert len(maprows) <= 1, "Tx Sig is primary key - find zero or one"

    if maprows:
        row = maprows[0]

        transaction_id = row["transaction_id"]

        # {'transaction_id': 1039639, 'slot': 234765028, 'error': 34, 'count': 1, 'utc_timestamp': datetime.datetime(2023, 12, 8, 18, 29, 23, 861619)}
        # note: slots may appear multiple times if there are multiple errors
        tx_errors_by_slots = invert_by_slot(
            postgres_connection.query(
            """
            SELECT
                tx_slot.slot,
                err.error_text,
                coalesce(sum(tx_slot.count),0) AS count
            FROM banking_stage_results_2.transaction_slot tx_slot
            INNER JOIN banking_stage_results_2.errors err ON err.error_code=tx_slot.error_code
            WHERE transaction_id=%s
            GROUP BY slot, err.error_text
            """, args=[transaction_id]))

        # ordered by slots ascending
        relevant_slots = tx_errors_by_slots.keys()

        row["relevant_slots"] = relevant_slots

        row["tx_errors_by_slots"] = tx_errors_by_slots

        block_details_per_slot = dict()
        write_lock_info = dict()
        read_lock_info = dict()
        for relevant_slot in relevant_slots:

            # note: sort order will be defined later
            # note: amb vs amt:
            # * relation does not exist if the transaction was not included
            # * in this case the accounts are show but without the infos like prio fee
            # * accounts linked via amt have no slot relation and thus appear redundantly for all slots
            # * see tx ACQLVWCGhLurkcPp8a2QfaK9rpoe3opcbWa1TBtijhbQ3X6rMYpDcUaa9usY4b4fwj5pgTWj85wew7WhCEyTHBN for example
            # * is_write_locked and is_account_write_locked must be the same
            all_accountinfos = (
                postgres_connection.query(
                    """
                    SELECT
                     amt.is_writable AS is_account_write_locked,
                     acc.account_key,
                     amb.*
                    FROM banking_stage_results_2.accounts_map_transaction amt
                    INNER JOIN banking_stage_results_2.accounts acc ON acc.acc_id=amt.acc_id
                    LEFT JOIN banking_stage_results_2.accounts_map_blocks amb ON amb.acc_id=amt.acc_id AND amb.slot=%s
                    WHERE amt.transaction_id = %s
                    ORDER BY amb.total_cu_consumed DESC NULLS LAST, amt.acc_id
                    """, args=[relevant_slot, transaction_id]))

            related_blocks = recent_blocks_database.run_query(filter_slot=relevant_slot)
            if len(related_blocks) != 1:
                raise Exception("Expected exactly one block for slot %s" % relevant_slot)
            block_details = related_blocks[0]
            block_details_per_slot[relevant_slot] = block_details

            account_info_expanded = []
            for account_info in all_accountinfos:
                # slot is set if amb relation exists i.e. if the tx was included
                maybe_slot = account_info['slot']

                if maybe_slot is None:
                    info = {
                        'key': account_info['account_key'],
                        'is_account_write_locked': account_info['is_account_write_locked'],
                        'cu_requested': None,
                        'cu_consumed': None,
                        'min_pf': None,
                        'median_pf': None,
                        'max_pf': None,
                    }
                    account_info_expanded.append(info)
                else:
                    prio_fee_data = json.loads(account_info['prioritization_fees_info'])
                    info = {
                        'key': account_info['account_key'],
                        'is_account_write_locked': account_info['is_account_write_locked'],
                        'cu_requested': account_info['total_cu_requested'],
                        'cu_consumed': account_info['total_cu_consumed'],
                        'min_pf': prio_fee_data['min'],
                        'median_pf': prio_fee_data['med'],
                        'max_pf': prio_fee_data['max']
                    }
                    account_info_expanded.append(info)

            write_lock_info[relevant_slot] = [acc for acc in account_info_expanded if acc['is_account_write_locked'] is True]
            read_lock_info[relevant_slot] = [acc for acc in account_info_expanded if acc['is_account_write_locked'] is False]

        row["block_details_per_slot"] = block_details_per_slot
        row["write_lock_info"] = write_lock_info
        row["read_lock_info"] = read_lock_info

    # note: effectively this is always one row
    return maprows


# see https://codereview.stackexchange.com/questions/188918/creating-an-inverted-index-in-python
#  {'slot': 233397518, 'key': 'Ap5pxfhTsW8bW4SvbezbrGdaSWRDmNSMycgCu11ba4i', 'cu_requested': 700000, 'cu_consumed': 53861, 'max_pf': 1, 'min_pf': 0, 'median_pf': 1}
def invert_by_slot(rows):
    inv_indx = defaultdict(list)
    for row in rows:
        inv_indx[row["slot"]].append(row)
    return inv_indx


