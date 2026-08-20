
# models/transaction.py

from pydantic import BaseModel, Field
from typing import Optional


class Transaction(BaseModel):
    user_id: str
    transaction_id: str
    amount: float = Field(gt=0)

    merchant_id: Optional[str] = None
    location: Optional[str] = None
    device_id: Optional[str] = None

    transaction_hour: int = Field(ge=0, le=23)

    previous_transaction_amount: float = 0.0
    average_transaction_amount: float = 0.0

    failed_attempts: int = 0
    new_device: bool = False
    new_location: bool = False