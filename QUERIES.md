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

### Blocks sent from banking stage error plugin and the respective leader
```sql
SELECT slot,leader_identity,utc_timestamp FROM banking_stage_results_2.transaction_slot tx_slot
INNER JOIN banking_stage_results_2.blocks using (slot)
order by slot desc
```


### Transactions with info and slot
**note:** the detail query LEFT JOINs on transaction_slot while the list query INNER JOINs 

#### transaction details
```sql
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
LEFT JOIN banking_stage_results_2.transaction_slot tx_slot USING (transaction_id)
LEFT JOIN banking_stage_results_2.transaction_infos txi USING (transaction_id)
WHERE signature = '4HBpgB8TPJ54iH2hJgNQ1i5hhB7F3P7hhsHySt8wLhBkJp4xLfynDuZgZtLLGywTKcLtbEYHi7sd6NYp4jDCMd41'
  AND (tx_slot IS NOT NULL OR txi IS NOT NULL)
ORDER BY utc_timestamp DESC, transaction_id DESC
```

#### tx-error page
```sql
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
INNER JOIN banking_stage_results_2.transaction_slot tx_slot USING (transaction_id)
LEFT JOIN banking_stage_results_2.transaction_infos txi USING (transaction_id)
ORDER BY utc_timestamp DESC, transaction_id DESC
LIMIT 100
```