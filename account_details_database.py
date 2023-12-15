import transaction_database
import postgres_connection
import json


def build_account_details(pubkey: str, recent_blocks_row_limit=10):
    (transactions, is_limit_exceeded) = list(transaction_database.query_transactions_by_address(pubkey))
    account = {'pubkey': pubkey}

    blocks = postgres_connection.query(
        """
            SELECT
                slot,
                total_cu_consumed,
                prioritization_fees_info
            FROM banking_stage_results_2.accounts_map_blocks b
            INNER JOIN banking_stage_results_2.accounts acc ON acc.acc_id=b.acc_id
            WHERE b.is_write_locked AND account_key = %s
            ORDER BY slot DESC
            limit %s
        """, args=[pubkey, recent_blocks_row_limit])
    for row in blocks:
        pf = json.loads(row['prioritization_fees_info'])
        row['min'] = pf['min']
        row['med'] = pf['med']
        row['max'] = pf['max']
        row['p75'] = pf['p75']
        row['p90'] = pf['p90']
        row['p95'] = pf['p95']
    return account, blocks, transactions, is_limit_exceeded
    
def main():
    build_account_details('AfASDKLEWG7Di9HtZDmHKftR1fsMXBtTSxP7qMo9qv7L')


