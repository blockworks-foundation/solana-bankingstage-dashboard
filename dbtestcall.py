import math
import pg8000.native

def RunQuery():
    # con = pg8000.native.Connection('postgres', password='postgres', host='localhost', port=5432, database='da11copy')
    con = pg8000.native.Connection('query_user', password='Udoz4nahbeethohb', host='localhost', port=5432, database='da11copy')
    result = con.run(
        """
        SELECT * FROM (
            SELECT
                signature,  RTRIM(NULLIF(errors, '')) as errors,
                is_executed, is_confirmed,
                cu_requested, prioritization_fees
            FROM banking_stage_results.transaction_infos
        ) AS data
        WHERE errors is not null
        """)

    maprows = []
    for row in result:
        data = dict()
        data['signature'] = row[0]
        data['errors'] = row[1]
        # data['errors_array'] = row[1].split(';')
        data['is_executed'] = row[2]
        data['is_confirmed'] = row[3]
        data['cu_requested'] = row[4]
        data['prioritization_fees'] = row[5]
        # print(data)
        maprows.append(data)
    return maprows

def Main():
    RunQuery()

if __name__=="__main__":
    Main()

