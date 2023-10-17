import math
from typing import Union, Any

import pg8000.native

def RunQuery():
    con = pg8000.dbapi.Connection('query_user', password='Udoz4nahbeethohb', host='localhost', port=5432, database='da11copy')
    c = con.cursor()
    c.execute(
        """
        SELECT * FROM (
            SELECT
                ROW_NUMBER() OVER () AS pos,
                signature,
                message,
                errors,
                is_executed,
                is_confirmed,
                first_notification_slot,
                cu_requested,
                prioritization_fees,
                "timestamp",
                accounts_used
            FROM banking_stage_results.transaction_infos
        ) AS data
        WHERE true
        ORDER BY "timestamp"
        """)

    rows = c.fetchall()
    keys = [k[0] for k in c.description]
    maprows = [dict(zip(keys, row)) for row in rows]
    print(maprows)


    return maprows

def Main():
    RunQuery()

if __name__=="__main__":
    Main()

