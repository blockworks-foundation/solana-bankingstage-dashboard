import transaction_database
import postgres_connection
import json

def build_account_details(pubkey: str):
    (transactions, is_limit_exceeded) = list(transaction_database.query_transactions_by_address(pubkey))
    account = {}
    account['pubkey'] = pubkey

    blocks = postgres_connection.query(
        """
        SELECT * FROM (
            SELECT
                slot,
                total_cu_consumed,
                prioritization_fees_info
            FROM banking_stage_results_2.accounts_map_blocks
            WHERE acc_id = (select acc_id from banking_stage_results_2.accounts where account_key = %s) and is_write_locked = true
            order by slot desc
            limit 10
        ) AS data
        """, args=[pubkey])
    for row in blocks:
        pf = json.loads(row['prioritization_fees_info'])
        row['min'] = pf['min']
        row['med'] = pf['med']
        row['max'] = pf['max']
        row['p75'] = pf['p75']
        row['p90'] = pf['p90']
        row['p95'] = pf['p95']
    account['blocks'] = blocks
    return (account, transactions, is_limit_exceeded)
    
def main():
    build_account_details('AfASDKLEWG7Di9HtZDmHKftR1fsMXBtTSxP7qMo9qv7L')


