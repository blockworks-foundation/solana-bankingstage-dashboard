import postgres_connection
import json


def run_query():
    maprows = postgres_connection.query(
        """
        SELECT
            *
        FROM (
            SELECT
                signature,
                (
                    SELECT ARRAY_AGG(json_object('error' VALUE err.error,'count':count)::text)
                    FROM banking_stage_results_2.transaction_slot tx_slot
                    INNER JOIN banking_stage_results_2.errors err ON err.error_code=tx_slot.error
                    WHERE tx_slot.transaction_id=txi.transaction_id
                ) AS all_errors,
                is_successful,
                processed_slot,
                (
                    SELECT min(slot)
                    FROM banking_stage_results_2.transaction_slot tx_slot
                    WHERE tx_slot.transaction_id=txi.transaction_id
                ) AS first_notification_slot,
                cu_requested,
                prioritization_fees,
                (
                    SELECT min(utc_timestamp)
                    FROM banking_stage_results_2.transaction_slot tx_slot
                    WHERE tx_slot.transaction_id=txi.transaction_id
                ) AS utc_timestamp
            FROM banking_stage_results_2.transaction_infos txi
            INNER JOIN banking_stage_results_2.transactions txs ON txs.transaction_id=txi.transaction_id
            WHERE true
        ) as data
        ORDER BY processed_slot, utc_timestamp, signature DESC
        LIMIT 50
        """)

    # print some samples
    # for row in maprows[:3]:
    #     print(row)
    # print("...")

    for index, row in enumerate(maprows):
        row['pos'] = index + 1
        map_jsons_in_row(row)
        map_timestamp(row)

    return maprows


def find_transaction_by_sig(tx_sig: str):
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
            utc_timestamp
        FROM banking_stage_results.transaction_infos txi
        INNER JOIN tx_aggregated ON tx_aggregated.sig=txi.signature AND tx_aggregated.min_slot=txi.first_notification_slot
        """, args=[tx_sig])

    assert len(maprows) <= 1, "Tx Sig is primary key - find zero or one"

    for row in maprows:
        map_jsons_in_row(row)
        map_timestamp(row)

    return maprows


# TODO format to MON DD HH24:MI:SS.MS
def map_timestamp(row):
    row['timestamp_formatted'] = row['utc_timestamp']
    return row


def map_jsons_in_row(row):
    errors = []
    if row["all_errors"] is None:
        row["all_errors"] = []
        return
    for errors_json in row["all_errors"]:
        # {"{\"error\" : \"TransactionError::AccountInUse\", \"count\" : 1}"}
        errors.append(json.loads(errors_json))
    row["errors_array"] = errors

def main():
    run_query()


if __name__=="__main__":
    main()

