import math
from typing import Union, Any

import pg8000.native
import log_scale

# x: 0..1
# out: "80%"
def format_width(x):
    return format(100.0 * x, "#.1f") + '%'

def calc_bars(row):
    successful_transactions = row['successful_transactions']
    processed_transactions = row['processed_transactions']
    banking_stage_errors = row['banking_stage_errors']
    total = processed_transactions + banking_stage_errors
    if total > 0:
        row['hide_bar'] = False
        a = successful_transactions / total
        b = processed_transactions / total
        c = (processed_transactions + banking_stage_errors) / total # effectively 1.0

        print("a=", a, "b=", b, "c=", c)
        la = log_scale.invlog_scale(a)
        lb = log_scale.invlog_scale(b)
        lc = log_scale.invlog_scale(c)
        print("la=", la, "lb=", lb, "lc=", lc)

        row['bar_success'] = format_width(la)
        row['bar_txerror'] = format_width(lb - la)
        row['bar_bankingerror'] = format_width(lc - lb)
        print(row['bar_success'], row['bar_txerror'], row['bar_bankingerror'])
    else:
        row['hide_bar'] = True

    # successful_transactions::real / (processed_transactions + banking_stage_errors)::real as bar_success,
    # (processed_transactions - successful_transactions)::real / (processed_transactions + banking_stage_errors)::real as bar_txerror,
    # banking_stage_errors::real / (processed_transactions + banking_stage_errors)::real as bar_bankingerror


def RunQuery():
    con = pg8000.dbapi.Connection('query_user', password='Udoz4nahbeethohb', host='localhost', port=5432, database='da11copy')
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

    # print first 10 rows
    if True:
        for row in maprows[:10]:
            print(row)
        print("...")

        for row in maprows:
            calc_bars(row)

    return maprows

def Main():
    RunQuery()

if __name__=="__main__":
    Main()

