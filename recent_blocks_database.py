import math
from typing import Union, Any

import pg8000.native

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
        ) AS data
        """)

    keys = [k[0] for k in cursor.description]
    maprows = [dict(zip(keys, row)) for row in cursor]

    # print first 10 rows
    if True:
        for row in maprows[:10]:
            print(row)
        print("...")

    return maprows

def Main():
    RunQuery()

if __name__=="__main__":
    Main()

