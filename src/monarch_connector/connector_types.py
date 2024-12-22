from pydantic import BaseModel
from api_types import Transaction


class AmazonOrder(BaseModel):
    order_date: str
    total_cost: str
    items: list[str]

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
