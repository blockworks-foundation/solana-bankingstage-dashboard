import postgres_connection
import json
import transaction_database
from collections import defaultdict


def find_transaction_details_by_sig(tx_sig: str):
    # transaction table primary key is used
    maprows = postgres_connection.query(
        """
        SELECT
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


    return maprows


# see https://codereview.stackexchange.com/questions/188918/creating-an-inverted-index-in-python
#  {'slot': 233397518, 'key': 'Ap5pxfhTsW8bW4SvbezbrGdaSWRDmNSMycgCu11ba4i', 'cu_requested': 700000, 'cu_consumed': 53861, 'max_pf': 1, 'min_pf': 0, 'median_pf': 1}
def invert_by_slot(rows):
    inv_indx = defaultdict(list)
    for row in rows:
        inv_indx[row["slot"]].append(row)
    return inv_indx
