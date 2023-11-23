import postgres_connection


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

    return maprows


def main():
    find_block_by_slotnumber(226352855)


if __name__=="__main__":
    main()

