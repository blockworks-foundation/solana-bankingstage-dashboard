import postgres_connection
import json

TXLIST_ROW_LIMIT = 50

def run_query(filter_txsig=None):
    maprows = postgres_connection.query(
        """
        SELECT * FROM (
            SELECT
                signature,
                (
                    SELECT ARRAY_AGG(json_build_object('error', err.error_text, 'count', count)::text)
                    FROM banking_stage_results_2.transaction_slot tx_slot
                    INNER JOIN banking_stage_results_2.errors err ON err.error_code=tx_slot.error_code
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
                AND (%s or signature = %s)
        ) as data
        ORDER BY processed_slot, utc_timestamp, signature DESC
        LIMIT 50
        """, [
            filter_txsig is None, filter_txsig,
        ])

    for index, row in enumerate(maprows):
        row['pos'] = index + 1
        map_jsons_in_row(row)

    return maprows


def find_transaction_by_sig(tx_sig: str):
    maprows = run_query(filter_txsig=tx_sig)

    assert len(maprows) <= 1, "Signature is primary key - find zero or one"

    return maprows


def map_jsons_in_row(row):
    errors = []
    if row["all_errors"] is None:
        row["all_errors"] = []
        return
    for errors_json in row["all_errors"]:
        # {"{\"error_text\" : \"TransactionError::AccountInUse\", \"count\" : 1}"}
        errors.append(json.loads(errors_json))
    row["errors_array"] = errors

def main():
    run_query()


if __name__=="__main__":
    main()

