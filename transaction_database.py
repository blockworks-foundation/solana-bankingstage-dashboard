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
                to_char(utc_timestamp, 'MON DD HH24:MI:SS.MS') as timestamp_formatted,
                accounts_used
            FROM banking_stage_results.transaction_infos
            WHERE true
            ORDER BY utc_timestamp DESC
            LIMIT 500
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
                to_char(utc_timestamp, 'MON DD HH24:MI:SS.MS') as timestamp_formatted,
                accounts_used
            FROM banking_stage_results.transaction_infos
            WHERE signature = %s
        ) AS data
        """, args=[tx_sig])

    assert len(maprows) <= 1, "Tx Sig is primary key - find zero or one"

    for row in maprows:
        map_jsons_in_row(row)
    return maprows


def map_jsons_in_row(row):
    if row['errors']:
        row['errors_array'] = json.loads(row['errors'])
    if row['accounts_used']:
        accounts = json.loads(row['accounts_used'])
        row['writable_accounts_used'] = list(map(lambda x: x['key'], filter(lambda x: x['writable'] == True, accounts)))
        row['readable_accounts_used'] = list(map(lambda x: x['key'], filter(lambda x: x['writable'] == False, accounts)))


def main():
    run_query()

if __name__=="__main__":
    main()

