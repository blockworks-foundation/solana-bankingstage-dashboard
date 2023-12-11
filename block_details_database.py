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
                        count(tx_slot.error)
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
    print("maprows", maprows)

    for row in maprows:
        slot = row["slot"]

        row['supp_infos'] = json.loads(row['supp_infos'])

        # note: sort order is undefined
        accountinfos =(
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

        row["heavily_writelocked_accounts_parsed"] = [acc for acc in account_info_expanded if acc['is_write_locked'] is True]
        row["heavily_readlocked_accounts_parsed"] = [acc for acc in account_info_expanded if acc['is_write_locked'] is False]

    return maprows



# parse (k:GubTBrbgk9JwkwX1FkXvsrF1UC2AP7iTgg8SGtgH14QE, cu_req:600000, cu_con:2243126)
# def parse_accounts(acc):
#     groups = re.match(r"\((k:)(?P<k>[a-zA-Z0-9]+)(, cu_req:)(?P<cu_req>[0-9]+)(, cu_con:)(?P<cu_con>[0-9]+)\)", acc)
#     return (groups.group('k'), groups.group('cu_req'), groups.group('cu_con'))

def main():
    find_block_by_slotnumber(226352855)


