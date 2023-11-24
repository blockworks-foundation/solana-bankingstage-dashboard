import postgres_connection
import json

def run_query():
    con = postgres_connection.create_connection()
    cursor = con.cursor()
    cursor.execute(
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
            LIMIT 50
        ) AS data
        """)

    keys = [k[0] for k in cursor.description]
    maprows = [dict(zip(keys, row)) for row in cursor]

    # print some samples
    # for row in maprows[:3]:
    #     print(row)
    # print("...")

    for index, row in enumerate(maprows):
        row['pos'] = index + 1
        row['errors_array'] = json.loads(row['errors'])
        row['accounts_used_array'] = json.loads(row['accounts_used'])

    return maprows


def find_transaction_by_sig(tx_sig: str):
    con = postgres_connection.create_connection()
    cursor = con.cursor()
    # transaction table primary key is uses
    cursor.execute(
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

    keys = [k[0] for k in cursor.description]
    maprows = [dict(zip(keys, row)) for row in cursor]

    assert len(maprows) <= 1, "Tx Sig is primary key - find zero or one"

    for row in maprows:
        row['errors_array'] = json.loads(row['errors'])
        row['accounts_used_array'] = json.loads(row['accounts_used'])

    return maprows


def main():
    run_query()

if __name__=="__main__":
    main()

