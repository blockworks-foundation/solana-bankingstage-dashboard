import postgres_connection
import json

def run_query(transaction_row_limit=None, filter_txsig=None, filter_account_address=None):
    maprows = postgres_connection.query(
        """
        SELECT * FROM (
            SELECT
				signature,
				( SELECT count(distinct slot) FROM banking_stage_results_2.transaction_slot WHERE transaction_id=tx_slot.transaction_id ) AS num_relative_slots,
				(
					SELECT ARRAY_AGG(json_build_object('error', err.error_text, 'count', count)::text)
					FROM banking_stage_results_2.errors err
					WHERE err.error_code=tx_slot.error_code
				) AS all_errors,
				( txi is not null ) AS was_included_in_block,
				txi.cu_requested,
				txi.prioritization_fees,
				utc_timestamp
            FROM banking_stage_results_2.transaction_slot tx_slot
            INNER JOIN banking_stage_results_2.transactions txs ON txs.transaction_id=tx_slot.transaction_id
			LEFT JOIN banking_stage_results_2.transaction_infos txi ON txi.transaction_id=tx_slot.transaction_id
            WHERE true
                AND (%s or signature = %s)
                AND (%s or txi.transaction_id in (
						SELECT transaction_id
						FROM banking_stage_results_2.accounts_map_transaction amt
						INNER JOIN banking_stage_results_2.accounts acc ON acc.acc_id=amt.acc_id
						WHERE account_key = %s
					))
        ) AS data
        ORDER BY utc_timestamp DESC
        LIMIT %s
        """, [
            filter_txsig is None, filter_txsig,
            filter_account_address is None, filter_account_address,
            transaction_row_limit or 50,
        ])

    for index, row in enumerate(maprows):
        row['pos'] = index + 1
        map_jsons_in_row(row)

    return maprows


def find_transaction_by_sig(tx_sig: str):
    maprows = run_query(transaction_row_limit=10, filter_txsig=tx_sig)

    assert len(maprows) <= 1, "Signature is primary key - find zero or one"

    return maprows


# return (rows, is_limit_exceeded)
def query_transactions_by_address(account_key: str) -> (list, bool):
    maprows = run_query(transaction_row_limit=501, filter_account_address=account_key)

    if len(maprows) == 501:
        print("limit exceeded while searching for transactions by address")
        return maprows, True

    return maprows, False


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

