from typing import Optional
from pydantic import BaseModel
from .api_types import Transaction


# We choose to effectively redefine AmazonOrderData here because
#   AmazonOrderData is used to validate CSV data, and thus may
#   have undefined fields. We want to enforce that the fields
#   are defined here and thus redefine the class.
#
#   Important: This means that changes to either one of the classes
#              are likely to require modifying the other class.
class AmazonOrder(BaseModel):
    order_date: str
    total_cost: str
    items: list[str]
    account_email: Optional[str] = None

    def __str__(self):
        return f"Order: {self.order_date} for {self.total_cost} with {len(self.items)} items"

    def __repr__(self):
        return f"Order: {self.order_date} for {self.total_cost} with {len(self.items)} items"


class TransactionAmazonMapping(BaseModel):
    transaction: Transaction
    amazon_orders: list[AmazonOrder]

    def __str__(self):
        return f"Transaction: {self.transaction.plaidName} for {self.transaction.amount} on {self.transaction.date} with {len(self.amazon_orders)} Amazon orders"

    def __repr__(self):
        return f"Transaction: {self.transaction.plaidName} for {self.transaction.amount} on {self.transaction.date} with {len(self.amazon_orders)} Amazon orders"
