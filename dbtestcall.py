import math
import pg8000.native

def Main():
    # con = pg8000.native.Connection('postgres', password='postgres', host='localhost', port=5432, database='da11copy')
    con = pg8000.native.Connection('query_user', password='Udoz4nahbeethohb', host='localhost', port=5432, database='da11copy')
    result = con.run(
        """
        SELECT
            signature, RTRIM(NULLIF(errors, '')) as errors,
            is_executed, is_confirmed,
            cu_requested, prioritization_fees
        FROM banking_stage_results.transaction_infos
        """)
    for row in result:
        print(row)

if __name__=="__main__":
    Main()

