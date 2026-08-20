cursor.execute(

"""

SELECT AVG(amount)

FROM transactions

"""

)

average = cursor.fetchone()[0]

if average:

    if tx.amount > average * 2:

        risk += 10