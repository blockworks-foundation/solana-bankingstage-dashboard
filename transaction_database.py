import postgres_connection
import json


def run_query():
    maprows = postgres_connection.query(
        """
        WITH tx_aggregated AS (
            SELECT
                signature as sig,
                min(first_notification_slot) as min_slot,
                ARRAY_AGG(errors) as all_errors
            FROM banking_stage_results.transaction_infos
            WHERE true
            GROUP BY signature
            ORDER BY min(utc_timestamp)
            LIMIT 50
        )
        SELECT
            signature,
            tx_aggregated.all_errors,
            is_executed,
            is_confirmed,
            first_notification_slot,
            cu_requested,
            prioritization_fees,
            utc_timestamp,
            -- e.g. "OCT 17 12:29:17.5127"
            to_char(utc_timestamp, 'MON DD HH24:MI:SS.MS') as timestamp_formatted
        FROM banking_stage_results.transaction_infos txi
        INNER JOIN tx_aggregated ON tx_aggregated.sig=txi.signature AND tx_aggregated.min_slot=txi.first_notification_slot
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


def map_jsons_in_row(row):
    errors = []
    # flatmap postgres array of json strings which contain array (of errors, usually one)
    for errors_json in row["all_errors"]:
        for error in json.loads(errors_json):
            errors.append(error)
    row["errors_array"] = errors

def main():
    run_query()


if __name__=="__main__":
    main()

