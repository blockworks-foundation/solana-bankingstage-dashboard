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
    txerrors = processed_transactions - successful_transactions
    row['txerrors'] = txerrors


def calc_bar_block_content(row):
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


def calc_bar_block_fill(row):
    total_cu_used = row['total_cu_used']
    total_cu_unused = 48000000 - total_cu_used
    total = 48000000
    a = total_cu_used / total
    b = total_cu_unused / total

    row['bar_cu_consumed'] = format_width_percentage(a)
    row['bar_cu_unused'] = format_width_percentage(b)
    row['total_cu_used_mn'] = format(total_cu_used / 1000000, "#.1f") + "M"


def run_query(to_slot=None, blocks_row_limit=100, filter_slot=None, filter_blockhash=None):
    maprows = postgres_connection.query(
        """
        SELECT * FROM (
            SELECT
                slot,
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
            WHERE true
                AND (%s or slot <= %s)
                AND (%s or slot = %s)
                AND (%s or block_hash = %s)
            ORDER BY slot DESC
            LIMIT %s
        ) AS data
        """,
        [
            to_slot is None, to_slot,
            filter_slot is None, filter_slot,
            filter_blockhash is None, filter_blockhash,
            blocks_row_limit,
        ])

    for row in maprows:
        calc_bar_block_content(row)
        calc_bar_block_fill(row)
        calc_figures(row)
        row["prioritization_fees"] = json.loads(row['supp_infos'])

    return maprows


def search_block_by_slotnumber(slot_number: int):
    maprows = run_query(filter_slot=slot_number, blocks_row_limit=20)

    assert len(maprows) <= 1, "Slot is primary key - find zero or one"

    return maprows


def search_block_by_blockhash(block_hash: str):
    maprows = run_query(filter_blockhash=block_hash, blocks_row_limit=20)

    assert len(maprows) <= 1, "Block hash is unique - find zero or one"

    return maprows


def main():
    run_query()


if __name__=="__main__":
    main()

