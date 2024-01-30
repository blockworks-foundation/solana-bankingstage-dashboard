import postgres_connection
import json


def run_query(transaction_row_limit=50, filter_txsig=None):
    maprows = postgres_connection.query(
        """
        SELECT * FROM (
            SELECT
                signature,
                txi.transaction_id,
                ( SELECT count(distinct slot) FROM banking_stage_results_2.transaction_slot WHERE transaction_id=tx_slot.transaction_id ) AS num_relative_slots,
                (
                   SELECT ARRAY_AGG(json_build_object('slot', tx_slot.slot, 'error', err.error_text, 'count', count)::text)
                   FROM banking_stage_results_2.errors err
                   WHERE err.error_code=tx_slot.error_code
               ) AS all_errors,
               tx_slot.utc_timestamp,
               -- optional fields from transaction_infos
               ( txi is not null ) AS was_included_in_block,
               txi.cu_requested,
               txi.prioritization_fees
            FROM banking_stage_results_2.transactions txs
            INNER JOIN banking_stage_results_2.transaction_slot tx_slot ON tx_slot.transaction_id=txs.transaction_id
            LEFT JOIN banking_stage_results_2.transaction_infos txi ON txi.transaction_id=tx_slot.transaction_id
            WHERE true
                AND (%s or signature = %s)
        ) AS data
        -- transaction_id is required as tie breaker
        ORDER BY utc_timestamp DESC, transaction_id DESC
        LIMIT %s
        """, [
            filter_txsig is None, filter_txsig,
            transaction_row_limit,
        ])

    for index, row in enumerate(maprows):
        row['pos'] = index + 1
        map_jsons_in_row(row)

    return maprows


def query_transactions_by_address(account_key: str, transaction_row_limit=1000):
    maprows = postgres_connection.query(
    """
        WITH tx_slot_data AS (
            SELECT
                transaction_id,
                min(slot) AS first_slot,
                min(utc_timestamp) AS min_utc_timestamp
            FROM banking_stage_results_2.transaction_slot tx_slot
            GROUP BY transaction_id
        )
        SELECT
           amt_txs.transaction_id,
           sort_nr,
           signature,
           ( txi is not null ) AS was_included_in_block,
           txi.cu_requested,
           txi.prioritization_fees,
           tx_slot_data.min_utc_timestamp AS utc_timestamp
        FROM
        (
            -- unnest the array, remove duplicates keeping the first occurence (i.e. more recent transactions), the restore sort order and finally limit
            SELECT DISTINCT ON (acc_id,transaction_id) acc_id, transaction_id, sort_nr FROM (
                SELECT acc_id, unnested.transaction_id, unnested.sort_nr
                FROM banking_stage_results_2.accounts_map_transaction_latest amt_latest,
                    unnest(amt_latest.tx_ids) WITH ORDINALITY AS unnested(transaction_id, sort_nr)
                WHERE amt_latest.acc_id IN (SELECT acc_id FROM banking_stage_results_2.accounts WHERE account_key=%s)
            )
        ) as amt_txs
        INNER JOIN banking_stage_results_2.transactions txs ON txs.transaction_id=amt_txs.transaction_id
        LEFT JOIN tx_slot_data ON tx_slot_data.transaction_id=amt_txs.transaction_id
        LEFT JOIN banking_stage_results_2.transaction_infos txi ON txi.transaction_id=amt_txs.transaction_id
        WHERE true
            -- note: check for txi is actually useless ATM as txi is always updated aling with amt_latest
            AND (tx_slot_data IS NOT NULL OR txi IS NOT NULL)
        ORDER BY sort_nr
        LIMIT %s
        """, [
            account_key,
            # note: there is only a limited number of transaction ids per account stored in the postgres array amt_latest.tx_ids
            transaction_row_limit,
        ])

    for index, row in enumerate(maprows):
        row['pos'] = index + 1

    return maprows


# may return multiple rows
def search_transaction_by_sig(tx_sig: str):
    maprows = run_query(transaction_row_limit=10, filter_txsig=tx_sig)

    return maprows


# return (rows, is_limit_exceeded)
def search_transactions_by_address(account_key: str) -> (list, bool):
    page_size = 10
    maprows = query_transactions_by_address(transaction_row_limit=page_size+1, account_key=account_key)

    if len(maprows) == page_size+1:
        print("limit exceeded while searching for transactions by address")
        return maprows[:page_size], True

    return maprows, False


def map_jsons_in_row(row):
    errors = []
    if row["all_errors"] is None:
        row["all_errors"] = []
        return
    for errors_json in row["all_errors"]:
        errors.append(json.loads(errors_json))
    row["errors_array"] = errors


def main():
    run_query()


if __name__=="__main__":
    main()

