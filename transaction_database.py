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
                signature,
                message,
                errors,
                is_executed,
                is_confirmed,
                first_notification_slot,
                cu_requested,
                prioritization_fees,
                -- "OCT 17 12:29:17.5127"
                utc_timestamp,
                to_char(utc_timestamp, 'MON DD HH24:MI:SS.FF4') as timestamp_formatted,
                accounts_used
            FROM banking_stage_results.transaction_infos
            WHERE true
            ORDER BY utc_timestamp DESC
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
        row['errors_array'] = row['errors'].rstrip().split(';')

    return maprows

def Main():
    RunQuery()

if __name__=="__main__":
    Main()

