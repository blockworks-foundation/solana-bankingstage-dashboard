## Collection of useful(tm) queries

### List accounts referenced in the relevant slots for respective transaction
This is intended for testing or finding examples.

```sql
SELECT
 amt.transaction_id,
 acc.account_key,
 amb.*
FROM banking_stage_results_2.accounts_map_blocks amb
INNER JOIN banking_stage_results_2.accounts_map_transaction amt ON amt.acc_id=amb.acc_id
INNER JOIN banking_stage_results_2.accounts acc ON acc.acc_id=amb.acc_id
INNER JOIN banking_stage_results_2.transaction_slot tx_slot ON tx_slot.slot=amb.slot AND tx_slot.transaction_id=amt.transaction_id
```


### Transactions with more than one relevant slot

```sql
SELECT
 tx_slot.transaction_id,signature,
 count(distinct slot)
FROM banking_stage_results_2.transaction_slot tx_slot
INNER JOIN banking_stage_results_2.transactions txs ON txs.transaction_id=tx_slot.transaction_id
INNER JOIN banking_stage_results_2.errors err ON err.error_code=tx_slot.error_code
WHERE true
GROUP BY tx_slot.transaction_id, signature
HAVING count(distinct slot) > 1
```