import postgres_connection
import json
import transaction_database


def find_transaction_details_by_sig(tx_sig: str):
    # transaction table primary key is used
    maprows = postgres_connection.query(
        """
        SELECT * FROM (
            SELECT
                signature,
                errors,
                is_executed,
                is_confirmed,
                first_notification_slot,
                cu_requested,
                prioritization_fees,
                processed_slot,
                to_char(utc_timestamp, 'MON DD HH24:MI:SS.MS') as timestamp_formatted,
                accounts_used
            FROM banking_stage_results.transaction_infos
            WHERE signature = %s
        ) AS data
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
                    acc = acc[0]
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
                    acc = acc[0]
                    info['cu_requested'] = acc['cu_requested']
                    info['cu_consumed'] = acc['cu_consumed']
                    info['max_pf'] = acc['max_pf']
                    info['min_pf'] = acc['min_pf']
                    info['median_pf'] = acc['median_pf']
                    if len(acc) > 1:
                        print("WARNING: multiple accounts with same key in same block")
                rai.append(info)
        row['write_lock_info'] = wai
        row['read_lock_info'] = rai
    return maprows
