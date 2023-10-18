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
    banking_stage_errors = row['banking_stage_errors']
    txerrors = processed_transactions - successful_transactions
    row['txerrors'] = txerrors

def calc_bars(row):
    successful_transactions = row['successful_transactions']
    processed_transactions = row['processed_transactions']
    banking_stage_errors = row['banking_stage_errors']
    total = processed_transactions + banking_stage_errors
    if total > 0:
        row['hide_bar'] = False
        # absolute values in range [0,1]
        a = successful_transactions / total
        b = processed_transactions / total
        c = (processed_transactions + banking_stage_errors) / total # effectively 1.0

        # absolute values in range [0,1] - log scaled
        la = log_scale.invlog_scale(a)
        lb = log_scale.invlog_scale(b)
        lc = log_scale.invlog_scale(c)

        # relative values for the bar widths
        row['bar_success'] = format_width_percentage(la)
        row['bar_txerror'] = format_width_percentage(lb - la)
        row['bar_bankingerror'] = format_width_percentage(lc - lb)
    else:
        row['hide_bar'] = True


def run_query():
    con = postgres_connection.create_connection()
    cursor = con.cursor()
    cursor.execute(
        """
        SELECT * FROM (
            SELECT
                ROW_NUMBER() OVER () AS pos,
                slot,
                processed_transactions,
                successful_transactions,
                banking_stage_errors,
                total_cu_used,
                total_cu_requested
            FROM banking_stage_results.blocks
            WHERE true
            ORDER BY slot DESC
            LIMIT 30
        ) AS data
        """)

    keys = [k[0] for k in cursor.description]
    maprows = [dict(zip(keys, row)) for row in cursor]

    # print some samples
    for row in maprows[:3]:
        print(row)
    print("...")

    for row in maprows:
        calc_bars(row)
        calc_figures(row)

    return maprows


def main():
    run_query()


if __name__=="__main__":
    main()

