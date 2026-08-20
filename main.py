# services/upi_validator.py

import re


class UPIValidator:

    UPI_PATTERN = re.compile(
        r"^[a-zA-Z0-9._-]{2,256}@[a-zA-Z]{2,64}$"
    )

    @classmethod
    def validate(cls, upi_id: str):

        if not upi_id:
            return {
                "valid": False,
                "reason": "UPI ID is empty"
            }

        upi_id = upi_id.strip()

        if not cls.UPI_PATTERN.match(upi_id):

            return {
                "valid": False,
                "reason": "Invalid UPI ID format"
            }

        username, provider = upi_id.split("@", 1)

        return {
            "valid": True,
            "username": username,
            "provider": provider
        }


def validate_transaction_upi(
    sender_upi,
    receiver_upi
):

    sender = UPIValidator.validate(sender_upi)
    receiver = UPIValidator.validate(receiver_upi)

    return {
        "sender": sender,
        "receiver": receiver,
        "valid": (
            sender["valid"] and
            receiver["valid"]
        )
    }