# =========================================================
# SECUREFLOW-AI
# CODE 8 — DYNAMIC VERIFICATION
# =========================================================


def generate_verification_question(
    transaction,
    user
):
    """
    Generates a verification question based on
    the suspicious behaviour detected.
    """

    # -----------------------------------------------------
    # NEW DEVICE
    # -----------------------------------------------------

    if transaction.device != user["known_device"]:

        return {
            "type": "DEVICE_VERIFICATION",

            "question":
                "Are you currently using a new device for this transaction?"
        }


    # -----------------------------------------------------
    # NEW LOCATION
    # -----------------------------------------------------

    if transaction.location != user["known_location"]:

        return {
            "type": "LOCATION_VERIFICATION",

            "question":
                "Are you currently making this transaction from a new location?"
        }


    # -----------------------------------------------------
    # NEW BENEFICIARY
    # -----------------------------------------------------

    if transaction.beneficiary != user["known_beneficiary"]:

        return {
            "type": "BENEFICIARY_VERIFICATION",

            "question":
                "Did you intentionally make this payment to this new beneficiary?"
        }


    # -----------------------------------------------------
    # HIGH AMOUNT
    # -----------------------------------------------------

    if (
        user["average_amount"] > 0
        and
        transaction.amount >
        user["average_amount"] * 3
    ):

        return {
            "type": "AMOUNT_VERIFICATION",

            "question":
                "Did you personally initiate this high-value transaction?"
        }


    # -----------------------------------------------------
    # GENERAL VERIFICATION
    # -----------------------------------------------------

    return {
        "type": "GENERAL_VERIFICATION",

        "question":
            "Did you personally initiate this transaction?"
    }


# =========================================================
# VERIFICATION RESPONSE MODEL
# =========================================================

from pydantic import BaseModel


class VerificationRequest(BaseModel):

    transaction_id: int

    confirmed: bool


# =========================================================
# CREATE VERIFICATION
# =========================================================

@app.post("/api/verification")
def verify_transaction(
    verification: VerificationRequest
):

    connection = get_database()

    cursor = connection.cursor()


    # -----------------------------------------------------
    # FIND TRANSACTION
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE id = ?
        """,
        (verification.transaction_id,)
    )

    transaction = cursor.fetchone()


    if transaction is None:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )


    # -----------------------------------------------------
    # USER CONFIRMED
    # -----------------------------------------------------

    if verification.confirmed:

        decision = "ALLOW"

        message = (
            "Transaction verified by user and allowed."
        )


    # -----------------------------------------------------
    # USER REJECTED
    # -----------------------------------------------------

    else:

        decision = "BLOCK"

        message = (
            "Transaction rejected by user and blocked."
        )


    # -----------------------------------------------------
    # UPDATE DATABASE
    # -----------------------------------------------------

    cursor.execute(
        """
        UPDATE transactions

        SET decision = ?

        WHERE id = ?
        """,

        (
            decision,
            verification.transaction_id
        )
    )

    connection.commit()

    connection.close()


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "success": True,

        "transaction_id":
            verification.transaction_id,

        "decision":
            decision,

        "message":
            message

    }