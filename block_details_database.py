import postgres_connection
import json


def find_block_by_slotnumber(slot_number: int):
    maprows = postgres_connection.query(
        """
        SELECT * FROM (
            SELECT
                slot,
                block_hash,
                leader_identity,
                processed_transactions,
                successful_transactions,
                (
                    SELECT
                        coalesce(sum(tx_slot.count),0) as count
                    FROM banking_stage_results_2.transaction_slot tx_slot
                    WHERE tx_slot.slot=blocks.slot
                ) AS banking_stage_errors,
                total_cu_used,
                total_cu_requested,
                supp_infos
            FROM banking_stage_results_2.blocks
            -- this critera uses index idx_blocks_slot
            WHERE slot = %s
        ) AS data
        """, args=[slot_number])

    assert len(maprows) <= 1, "Slot is primary key - find zero or one"
    next_slot = (
        postgres_connection.query(
            """
            SELECT
                min(slot) as next_slot
            FROM banking_stage_results_2.blocks
            WHERE slot > %s
            """, args=[slot_number])
    )
    prev_slot = (
        postgres_connection.query(
            """
            SELECT
                max(slot) as prev_slot
            FROM banking_stage_results_2.blocks
            WHERE slot < %s
            """, args=[slot_number])
    )
    next_block = list(next_slot)[0]['next_slot']
    prev_block = list(prev_slot)[0]['prev_slot']

    if len(maprows) == 0:
        block = {}
        block["next_block"] = next_block
        block["prev_block"] = prev_block
        block["supp_infos"] = {}
        return block
    else:
        block = list(maprows)[0]
        slot = block["slot"]

        block['supp_infos'] = json.loads(block['supp_infos'])

        # note: sort order is undefined
        accountinfos = (
            postgres_connection.query(
                """
                SELECT
                    amb.*,
                    acc.account_key
                FROM banking_stage_results_2.accounts_map_blocks amb
                INNER JOIN banking_stage_results_2.accounts acc ON acc.acc_id=amb.acc_id
                WHERE slot = %s
                """, args=[slot])
        )
        account_info_expanded = []
        for account_info in accountinfos:
            prio_fee_data = json.loads(account_info['prioritization_fees_info'])
            info = {
                'slot': account_info['slot'],
                'key': account_info['account_key'],
                'is_write_locked': account_info['is_write_locked'],
                'cu_requested': account_info['total_cu_requested'],
                'cu_consumed': account_info['total_cu_consumed'],
                'min_pf': prio_fee_data['min'],
                'median_pf': prio_fee_data['med'],
                'max_pf': prio_fee_data['max']
            }
            account_info_expanded.append(info)
        account_info_expanded.sort(key=lambda acc: int(acc['cu_consumed']), reverse=True)

        block["heavily_writelocked_accounts_parsed"] = [acc for acc in account_info_expanded if acc['is_write_locked'] is True]
        block["heavily_readlocked_accounts_parsed"] = [acc for acc in account_info_expanded if acc['is_write_locked'] is False]
        block["next_block"] = next_block
        block["prev_block"] = prev_block
        return block


def is_matching_blockhash(block_hash):
    maprows = postgres_connection.query(
        """
            SELECT 1 FROM banking_stage_results_2.blocks
            WHERE block_hash = %s
        """, [block_hash])

    return len(maprows) > 0


def main():
    find_block_by_slotnumber(226352855)


