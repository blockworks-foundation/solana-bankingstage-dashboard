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
                banking_stage_errors,
                total_cu_used,
                total_cu_requested,
                heavily_writelocked_accounts,
                heavily_readlocked_accounts,
                supp_infos
            FROM banking_stage_results.blocks
            -- this critera uses index idx_blocks_slot
            WHERE slot = %s
        ) AS data
        """, args=[slot_number])

    assert len(maprows) <= 1, "Slot is primary key - find zero or one"

    for row in maprows:
        # format see BankingStageErrorsTrackingSidecar -> block_info.rs
        # parse (k:GubTBrbgk9JwkwX1FkXvsrF1UC2AP7iTgg8SGtgH14QE, cu_req:600000, cu_con:2243126)

        parsed_accounts = json.loads(row["heavily_writelocked_accounts"])
        row['supp_infos'] =json.loads(row['supp_infos'])
        parsed_accounts.sort(key=lambda acc: int(acc['cu_consumed']), reverse=True)
        row["heavily_writelocked_accounts_parsed"] = parsed_accounts
        # TODO need new parser

        parsed_accounts = json.loads(row["heavily_readlocked_accounts"])
        parsed_accounts.sort(key=lambda acc: int(acc['cu_consumed']), reverse=True)
        row["heavily_readlocked_accounts_parsed"] = parsed_accounts

    return maprows



# parse (k:GubTBrbgk9JwkwX1FkXvsrF1UC2AP7iTgg8SGtgH14QE, cu_req:600000, cu_con:2243126)
# def parse_accounts(acc):
#     groups = re.match(r"\((k:)(?P<k>[a-zA-Z0-9]+)(, cu_req:)(?P<cu_req>[0-9]+)(, cu_con:)(?P<cu_con>[0-9]+)\)", acc)
#     return (groups.group('k'), groups.group('cu_req'), groups.group('cu_con'))

def main():
    find_block_by_slotnumber(226352855)


