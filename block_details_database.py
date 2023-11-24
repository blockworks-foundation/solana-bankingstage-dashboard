import postgres_connection
import json
import re



def find_block_by_slotnumber(slot_number: int):
    con = postgres_connection.create_connection()
    cursor = con.cursor()
    cursor.execute(
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
                heavily_writelocked_accounts
            FROM banking_stage_results.blocks
            -- this critera uses index idx_blocks_slot
            WHERE slot = %s
        ) AS data
        """, args=[slot_number])

    keys = [k[0] for k in cursor.description]
    maprows = [dict(zip(keys, row)) for row in cursor]

    assert len(maprows) <= 1, "Slot is primary key - find zero or one"

    for row in maprows:
        # format see BankingStageErrorsTrackingSidecar -> block_info.rs
        # parse (k:GubTBrbgk9JwkwX1FkXvsrF1UC2AP7iTgg8SGtgH14QE, cu_req:600000, cu_con:2243126)

        parsed_accounts = []
        for acc in row["heavily_writelocked_accounts"]:
            (k, cu_req, cu_con) = parse_accounts(acc)
            parsed = {'k': k, 'cu_req': cu_req, 'cu_con': cu_con}
            parsed_accounts.append(parsed)

        parsed_accounts.sort(key=lambda acc: int(acc['cu_con']), reverse=True)
        row["heavily_writelocked_accounts_parsed"] = parsed_accounts

    return maprows



# parse (k:GubTBrbgk9JwkwX1FkXvsrF1UC2AP7iTgg8SGtgH14QE, cu_req:600000, cu_con:2243126)
def parse_accounts(acc):
    groups = re.match(r"\((k:)(?P<k>[a-zA-Z0-9]+)(, cu_req:)(?P<cu_req>[0-9]+)(, cu_con:)(?P<cu_con>[0-9]+)\)", acc)
    return (groups.group('k'), groups.group('cu_req'), groups.group('cu_con'))



def main():
    find_block_by_slotnumber(226352855)


def map_row_to_block_details():
    heavily_writelocked_accounts = r'{"(k:maCYbwXrJDnnP5ft3ySoH4ogwv5yFph8fFacgMa51de, cu_req:16000000, cu_con:1937292)","(k:C3zz2AutxkULZPafPdBrBLiuSV25AMi9vEqWjCsja4Dj, cu_req:400000, cu_con:1485802)","(k:GubTBrbgk9JwkwX1FkXvsrF1UC2AP7iTgg8SGtgH14QE, cu_req:400000, cu_con:1485802)"}'
    json_object = json.loads(heavily_writelocked_accounts)
    print("json_object", json_object)

if __name__=="__main__":
    map_row_to_block_details()

