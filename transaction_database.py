import postgres_connection


def run_query():
    con = postgres_connection.create_connection()
    cursor = con.cursor()
    cursor.execute(
        """
        SELECT * FROM (
            SELECT
                ROW_NUMBER() OVER () AS pos,
                signature,
                message,
                -- e.g. "Account in use-225558172:2;Account in use-225558173:1;"
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
    for row in maprows[:3]:
        print(row)
    print("...")

    for row in maprows:
        # note: type changed from 'text' to 'text[]'
        row['errors_array'] = row['errors']

    return maprows


def find_transaction_by_sig(tx_sig):
    con = postgres_connection.create_connection()
    cursor = con.cursor()
    cursor.execute(
        """
        SELECT * FROM (
            SELECT
                ROW_NUMBER() OVER () AS pos,
                signature,
                message,
                -- e.g. "Account in use-225558172:2;Account in use-225558173:1;"
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
        # note: type changed from 'text' to 'text[]'
        row['errors_array'] = row['errors']

    return maprows


def main():
    run_query()

if __name__=="__main__":
    main()

