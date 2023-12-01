import postgres_connection
import json


def run_query():
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
                utc_timestamp,
                -- e.g. "OCT 17 12:29:17.5127"
                to_char(utc_timestamp, 'MON DD HH24:MI:SS.MS') as timestamp_formatted
            FROM banking_stage_results.transaction_infos
            WHERE true
            ORDER BY utc_timestamp DESC
            LIMIT 50
        ) AS data
        """)

    # print some samples
    # for row in maprows[:3]:
    #     print(row)
    # print("...")

    for index, row in enumerate(maprows):
        row['pos'] = index + 1
        map_jsons_in_row(row)

    return maprows


def find_transaction_by_sig(tx_sig: str):
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
                utc_timestamp,
                -- e.g. "OCT 17 12:29:17.5127"
                to_char(utc_timestamp, 'MON DD HH24:MI:SS.MS') as timestamp_formatted
            FROM banking_stage_results.transaction_infos
            WHERE signature = %s
        ) AS data
        """, args=[tx_sig])

    assert len(maprows) <= 1, "Tx Sig is primary key - find zero or one"

    for row in maprows:
        map_jsons_in_row(row)
    return maprows

def find_transaction_by_sig_with_details(tx_sig: str):
    # transaction table primary key is uses
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
                utc_timestamp,
                to_char(utc_timestamp, 'MON DD HH24:MI:SS.MS') as timestamp_formatted,
                accounts_used
            FROM banking_stage_results.transaction_infos
            WHERE signature = %s
        ) AS data
        """, args=[tx_sig])

    assert len(maprows) <= 1, "Tx Sig is primary key - find zero or one"

    for row in maprows:
        map_jsons_in_row(row)    
        accounts = json.loads(row['accounts_used'])
        row['writelocked_accounts'] = list(filter(lambda x : x['writable'] == True, accounts))
        row['readlocked_accounts'] = list(filter(lambda x : x['writable'] == False, accounts))
        slots = {row['first_notification_slot']}
        for error in row['errors_array']:
            slots.add(error['slot'])
        row['slots'] = list(slots)

        slots_str = ','.join(map(str, slots))
        blockrows = postgres_connection.query(
        """
        SELECT * FROM (
            SELECT
                slot,
                heavily_writelocked_accounts,
                heavily_readlocked_accounts
            FROM banking_stage_results.blocks
            WHERE slot in (%s)
        ) AS data
        """, args=[slots_str])

        wai = []
        rai = []
        for block_data in blockrows:
            hwl = json.loads(block_data['heavily_writelocked_accounts'])
            hrl = json.loads(block_data['heavily_readlocked_accounts'])
            for writed in row['writelocked_accounts']:
                info = {'slot' : block_data['slot'], 'key' : writed['key'] }
                acc = list(filter(lambda x: x['key'] == writed['key'],hwl))
                if len(acc) > 0:
                    acc = acc[0]
                    info['cu_requested'] = acc['cu_requested']
                    info['cu_consumed'] = acc['cu_consumed']
                    info['max_pf'] = acc['max_pf']
                    info['min_pf'] = acc['min_pf']
                    info['median_pf'] = acc['median_pf']
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
                rai.append(info)
        row['write_lock_info'] = wai
        row['read_lock_info'] = rai
    return maprows

def map_jsons_in_row(row):
    if row['errors']:
        row['errors_array'] = json.loads(row['errors'])

def main():
    run_query()

if __name__=="__main__":
    main()

