import postgres_connection
import json
import transaction_database
from collections import defaultdict


def find_transaction_details_by_sig(tx_sig: str):
    # transaction table primary key is used
    maprows = postgres_connection.query(
        """
        SELECT
            min_transaction_id, max_transaction_id,
            tx_slot_agg.signature,
            tx_slot_agg.min_slot AS first_notification_slot,
            tx_slot_agg.min_utc_timestamp AS utc_timestamp,
            -- optional fields from transaction_infos
            txi.is_successful,
            txi.processed_slot,
            txi.cu_requested,
            txi.prioritization_fees
        FROM (
            SELECT
                signature, min(tx_slot.transaction_id) AS min_transaction_id, max(tx_slot.transaction_id) AS max_transaction_id,
                min(slot) AS min_slot, min(utc_timestamp) AS min_utc_timestamp
            FROM banking_stage_results_2.transaction_slot tx_slot
			INNER JOIN banking_stage_results_2.transactions txs ON txs.transaction_id=tx_slot.transaction_id
            LEFT JOIN banking_stage_results_2.transaction_infos txi ON txi.transaction_id=tx_slot.transaction_id
            WHERE txs.signature = %s
            GROUP BY signature
        ) as tx_slot_agg
        LEFT JOIN banking_stage_results_2.transaction_infos txi ON txi.transaction_id=tx_slot_agg.min_transaction_id
        """, args=[tx_sig])

    assert len(maprows) <= 1, "Tx Sig is primary key - find zero or one"

    if maprows:
        row = maprows[0]

        assert row["min_transaction_id"] == row["max_transaction_id"], "min_transaction_id and max_transaction_id must be equal"
        transaction_id = row["min_transaction_id"]

        # {'transaction_id': 1039639, 'slot': 234765028, 'error': 34, 'count': 1, 'utc_timestamp': datetime.datetime(2023, 12, 8, 18, 29, 23, 861619)}
        tx_slots = postgres_connection.query(
            """
            SELECT
             tx_slot.slot,
             err.error_text
            FROM banking_stage_results_2.transaction_slot tx_slot
            INNER JOIN banking_stage_results_2.errors err ON err.error_code=tx_slot.error_code
            WHERE transaction_id=%s
            """, args=[transaction_id])
        # ordered by slots ascending
        relevant_slots = [txslot["slot"] for txslot in tx_slots]

        row["relevant_slots"] = relevant_slots

        # note: sort order is undefined
        accountinfos_per_slot = (
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

        write_lock_info = dict()
        read_lock_info = dict()
        for relevant_slot in set(relevant_slots):
            accountinfos = accountinfos_per_slot.get(relevant_slot, [])

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
            account_info_expanded.sort(key=lambda acc: int(acc['cu_consumed']), reverse=True)
            write_lock_info[relevant_slot] = [acc for acc in account_info_expanded if acc['is_write_locked'] is True]
            read_lock_info[relevant_slot] = [acc for acc in account_info_expanded if acc['is_write_locked'] is False]

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


