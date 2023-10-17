import math
from typing import Union, Any

import pg8000.native


def calc_bars(row):
    successful_transactions = row['successful_transactions']
    processed_transactions = row['processed_transactions']
    banking_stage_errors = row['banking_stage_errors']
    total = processed_transactions + banking_stage_errors
    if total > 0:
        row['hide_bar'] = False
        row['bar_success'] = format(100.0 * successful_transactions / total, '#.1f') + '%'
        row['bar_txerror'] = format(100.0 * (processed_transactions - successful_transactions) / total, '#.1f') + '%'
        row['bar_bankingerror'] = format(100.0 * banking_stage_errors / total, '#.1f') + '%'
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

