import postgres_connection
import json
import transaction_database
from collections import defaultdict


def find_transaction_details_by_sig(tx_sig: str):
    # transaction table primary key is used
    maprows = postgres_connection.query(
        """
        WITH tx_aggregated AS (
            SELECT
                signature as sig,
                min(first_notification_slot) as min_slot,
                ARRAY_AGG(errors) as all_errors
            FROM banking_stage_results.transaction_infos
            WHERE signature = %s
            GROUP BY signature
        )
        SELECT
            signature,
            tx_aggregated.all_errors,
            is_executed,
            is_confirmed,
            first_notification_slot,
            cu_requested,
            prioritization_fees,
            processed_slot,
            to_char(utc_timestamp, 'MON DD HH24:MI:SS.MS') as timestamp_formatted,
            accounts_used
        FROM banking_stage_results.transaction_infos txi
        INNER JOIN tx_aggregated ON tx_aggregated.sig=txi.signature AND tx_aggregated.min_slot=txi.first_notification_slot
        """, args=[tx_sig])

    assert len(maprows) <= 1, "Tx Sig is primary key - find zero or one"

    for row in maprows:
        transaction_database.map_jsons_in_row(row)
        accounts = json.loads(row['accounts_used'])
        row['writelocked_accounts'] = list(filter(lambda acc : acc['writable'], accounts))
        row['readlocked_accounts'] = list(filter(lambda acc : not acc['writable'], accounts))
        relevent_slots_dict = {row['first_notification_slot']}
        for error in row['errors_array']:
            relevent_slots_dict.add(error['slot'])
        relevant_slots = list(relevent_slots_dict)
        row['relevant_slots'] = relevant_slots

        blockrows = postgres_connection.query(
            """
            SELECT * FROM (
                SELECT
                    slot,
                    heavily_writelocked_accounts,
                    heavily_readlocked_accounts
                FROM banking_stage_results.blocks
                -- see pg8000 docs for unnest hack
                WHERE slot IN (SELECT unnest(CAST(%s as bigint[])))
            ) AS data
            """, args=[relevant_slots])

        wai = []
        rai = []
        for block_data in blockrows:
            hwl = json.loads(block_data['heavily_writelocked_accounts'])
            hrl = json.loads(block_data['heavily_readlocked_accounts'])
            for writed in row['writelocked_accounts']:
                info = {'slot' : block_data['slot'], 'key' : writed['key'] }
                acc = list(filter(lambda acc_: acc_['key'] == writed['key'], hwl))
                if len(acc) > 0:
                    acc = defaultdict(lambda: 0, acc[0])
                    info['cu_requested'] = acc['cu_requested']
                    info['cu_consumed'] = acc['cu_consumed']
                    info['max_pf'] = acc['max_pf']
                    info['min_pf'] = acc['min_pf']
                    info['median_pf'] = acc['median_pf']
                    if len(acc) > 1:
                        print("WARNING: multiple accounts with same key in same block")
                wai.append(info)

            for readed in row['readlocked_accounts']:
                info = {'slot' : block_data['slot'], 'key' : readed['key'] }
                acc = list(filter(lambda x: x['key'] == readed['key'],hrl))
                if len(acc) > 0:
                    acc = defaultdict(lambda: 0, acc[0])
                    info['cu_requested'] = acc['cu_requested']
                    info['cu_consumed'] = acc['cu_consumed']
                    info['max_pf'] = acc['max_pf']
                    info['min_pf'] = acc['min_pf']
                    info['median_pf'] = acc['median_pf']
                    if len(acc) > 1:
                        print("WARNING: multiple accounts with same key in same block")
                rai.append(info)
        row['write_lock_info'] = invert_by_slot(wai)
        row['read_lock_info'] = invert_by_slot(rai)


    return maprows


# see https://codereview.stackexchange.com/questions/188918/creating-an-inverted-index-in-python
#  {'slot': 233397518, 'key': 'Ap5pxfhTsW8bW4SvbezbrGdaSWRDmNSMycgCu11ba4i', 'cu_requested': 700000, 'cu_consumed': 53861, 'max_pf': 1, 'min_pf': 0, 'median_pf': 1}
def invert_by_slot(rows):
    inv_indx = defaultdict(list)
    for row in rows:
        inv_indx[row["slot"]].append(row)
    return inv_indx
