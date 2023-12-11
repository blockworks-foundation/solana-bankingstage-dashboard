import json
import pg8000
import log_scale
import postgres_connection


# x: [0,1]
# out: "80.0%" (shown on html page and used for CSS width: 80%)
def format_width_percentage(x):
    return format(100.0 * x, "#.1f") + '%'


def calc_figures(row):
    successful_transactions = row['successful_transactions']
    processed_transactions = row['processed_transactions']
    banking_stage_errors = row['banking_stage_errors'] or 0
    txerrors = processed_transactions - successful_transactions
    row['txerrors'] = txerrors


def calc_bars(row):
    successful_transactions = row['successful_transactions']
    processed_transactions = row['processed_transactions']
    banking_stage_errors = row['banking_stage_errors'] or 0
    total = processed_transactions + banking_stage_errors
    if total > 0:
        row['hide_bar'] = False
        # absolute values in range [0,1]
        a = successful_transactions / total
        b = processed_transactions / total
        c = (processed_transactions + banking_stage_errors) / total # effectively 1.0

        # absolute values in range [0,1] - log scaled
        # la = log_scale.invlog_scale(a)
        # lb = log_scale.invlog_scale(b)
        # lc = log_scale.invlog_scale(c)
        # absolute values in range [0,1] - linear scale
        la = a
        lb = b
        lc = c

        # relative values for the bar labels (linear scale)
        row['bar_success'] = format_width_percentage(a)
        row['bar_txerror'] = format_width_percentage(b - a)
        row['bar_bankingerror'] = format_width_percentage(c - b)

        # relative values for the bar widths (log/linear scale)
        row['bar_success_scaled'] = format_width_percentage(la)
        row['bar_txerror_scaled'] = format_width_percentage(lb - la)
        row['bar_bankingerror_scaled'] = format_width_percentage(lc - lb)
    else:
        row['hide_bar'] = True


def run_query(to_slot=None):
    maprows = postgres_connection.query(
        """
        SELECT * FROM (
            SELECT
                slot,
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
            WHERE
                -- short circuit if true
                (%s or slot <= %s)
            ORDER BY slot DESC
            LIMIT 100
        ) AS data
        """,
        [to_slot is None, to_slot])

    for row in maprows:
        calc_bars(row)
        calc_figures(row)
        row["prioritization_fees"] = json.loads(row['supp_infos'])

    return maprows


def find_block_by_slotnumber(slot_number: int):
    maprows = postgres_connection.query(
        """
        SELECT * FROM (
            SELECT
                slot,
                processed_transactions,
                successful_transactions,
                banking_stage_errors,
                total_cu_used,
                total_cu_requested,
                supp_infos
            FROM banking_stage_results.blocks
            -- this critera uses index idx_blocks_slot
            WHERE slot = %s
        ) AS data
        """, args=[slot_number])

    assert len(maprows) <= 1, "Slot is primary key - find zero or one"

    for row in maprows:
        calc_bars(row)
        calc_figures(row)

    return maprows


def find_block_by_blockhash(block_hash: str):
    maprows = postgres_connection.query(
        """
        SELECT * FROM (
            SELECT
                slot,
                processed_transactions,
                successful_transactions,
                banking_stage_errors,
                total_cu_used,
                total_cu_requested,
                supp_infos
            FROM banking_stage_results.blocks
            -- uses index on primary key
            WHERE block_hash = %s
        ) AS data
        """, args=[block_hash])

    assert len(maprows) <= 1, "Block hash is unique - find zero or one"

    for row in maprows:
        calc_bars(row)
        calc_figures(row)

    print("found ", maprows, block_hash)

    return maprows


def main():
    run_query()


if __name__=="__main__":
    main()

