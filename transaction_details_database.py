import postgres_connection
import json
import transaction_database
from collections import defaultdict


def find_transaction_details_by_sig(tx_sig: str):
    # transaction table primary key is used
    maprows = postgres_connection.query(
        """
        SELECT
            txi.transaction_id,
            signature,
            '{}'::text[] all_errors,--  FIXME
            is_successful,
            processed_slot,
            --first_notification_slot,
            cu_requested,
            prioritization_fees,
            (
                SELECT min(utc_timestamp)
                FROM banking_stage_results_2.transaction_slot txslot
                WHERE txslot.transaction_id=txi.transaction_id
            ) AS utc_timestamp
        FROM banking_stage_results_2.transaction_infos txi
        INNER JOIN banking_stage_results_2.transactions txs ON txs.transaction_id=txi.transaction_id
        WHERE signature=%s
        """, args=[tx_sig])

    assert len(maprows) <= 1, "Tx Sig is primary key - find zero or one"

    # TODO this is only one row
    if maprows:
        row = maprows[0]

        # {'transaction_id': 1039639, 'slot': 234765028, 'error': 34, 'count': 1, 'utc_timestamp': datetime.datetime(2023, 12, 8, 18, 29, 23, 861619)}
        tx_slots = postgres_connection.query(
            """
            SELECT
             txslot.slot,
             txslot.error,
             err.error
            FROM banking_stage_results_2.transaction_slot txslot
            INNER JOIN banking_stage_results_2.errors err ON err.error_code=txslot.error
            WHERE transaction_id=%s
            """, args=[row["transaction_id"]])
        # ordered by slots ascending
        relevant_slots = set([txslot["slot"] for txslot in tx_slots])

        row["relevant_slots"] = relevant_slots

        accountinfos_per_slot =(
            invert_by_slot(
                postgres_connection.query(
                """
                SELECT
                 amb.*,
                 acc.account_key
                FROM banking_stage_results_2.accounts_map_blocks amb
                INNER JOIN banking_stage_results_2.accounts acc ON acc.acc_id=amb.acc_id
                WHERE slot IN (SELECT unnest(CAST(%s as bigint[])))
                """, args=[relevant_slots]))
        )

        # print("- transaction details for sig: " + tx_sig)
        # print("- relevant slots: " + str(relevant_slots))

        write_lock_info = dict()
        read_lock_info = dict()
        for relevant_slot in relevant_slots:
            accountinfos = accountinfos_per_slot.get(relevant_slot, [])
            # print("  - slot: ", relevant_slot)
            # print("  - errors in slot:")
            # for tx_slots_row in tx_slots:
            #     if tx_slots_row['slot'] == relevant_slot:
            #         print("    - " + tx_slots_row['error'])

            account_info_expanded = []
            for account_info in accountinfos:
                prio_fee_data = json.loads(account_info['prioritization_fees_info'])
                info = {
                    'slot': account_info['slot'],
                    'key': account_info['account_key'],
                    'is_write_locked': account_info['is_write_locked'],
                    'cu_requested': account_info['total_cu_requested'],
                    'cu_consumed': account_info['total_cu_consumed'],
                    'min_pf': prio_fee_data['min'],
                    'median_pf': prio_fee_data['med'],
                    'max_pf': prio_fee_data['max']
                }
                account_info_expanded.append(info)
            write_lock_info[relevant_slot] = [acc for acc in account_info_expanded if acc['is_write_locked'] is True]
            read_lock_info[relevant_slot] = [acc for acc in account_info_expanded if acc['is_write_locked'] is False]
            # for wli in write_lock_info[relevant_slot]:
            #     print("- write lock info: " + wli["key"])
            # for rli in read_lock_info[relevant_slot]:
            #     print("- read lock info: " + rli["key"])

        row["write_lock_info"] = write_lock_info
        row["read_lock_info"] = read_lock_info

    return maprows


# see https://codereview.stackexchange.com/questions/188918/creating-an-inverted-index-in-python
#  {'slot': 233397518, 'key': 'Ap5pxfhTsW8bW4SvbezbrGdaSWRDmNSMycgCu11ba4i', 'cu_requested': 700000, 'cu_consumed': 53861, 'max_pf': 1, 'min_pf': 0, 'median_pf': 1}
def invert_by_slot(rows):
    inv_indx = defaultdict(list)
    for row in rows:
        inv_indx[row["slot"]].append(row)
    return inv_indx
