from typing import Literal, Optional
from pydantic import BaseModel

class Merchant(BaseModel):
    name: str
    id: str
    transactionsCount: int

    def __str__(self):
        return f"Merchant: {self.name}"

    def __repr__(self):
        return f"Merchant: {self.name}"

class Account(BaseModel):
    id: str
    displayName: str

    def __str__(self):
        return f"Account: {self.displayName}"

    def __repr__(self):
        return f"Account: {self.displayName}"

class Category(BaseModel):
    id: str
    name: str

    def __str__(self):
        return f"Category: {self.name}"

    def __repr__(self):
        return f"Category: {self.name}"

class Transaction(BaseModel):
    id: str
    amount: float
    pending: bool
    date: str
    hideFromReports: bool
    plaidName: str
    notes: Optional[str] = None
    isRecurring: bool
    reviewStatus: Optional[Literal['needs_review'] | Literal['reviewed']] = None
    needsReview: bool
    attachments: list
    isSplitTransaction: bool
    createdAt: str
    updatedAt: str
    category: Category
    merchant: Merchant
    account: dict
    tags: list

    def __str__(self):
        return f"Transaction: {self.plaidName} for {self.amount} on {self.date}"

    def __repr__(self):
        return f"Transaction: {self.plaidName} for {self.amount} on {self.date}"


class AllTransactions(BaseModel):
    results: list[Transaction]

    def __str__(self):
        return f"Transactions: {self.results}"

    def __repr__(self):
        return f"Transactions: {self.results}"

class TransactionResponse(BaseModel):
    allTransactions: AllTransactions


class CategoryGroup(BaseModel):
    id: str
    name: str
    type: Literal['income'] | Literal['expense'] | Literal['transfer']


class CategoryDetails(BaseModel):
    id: str
    order: int
    name: str
    systemCategory: Optional[str] = None
    isSystemCategory: bool
    isDisabled: bool
    updatedAt: str
    createdAt: str
    group: CategoryGroup

class CategoriesResponse(BaseModel):
    categories: list[CategoryDetails]
    
    def __str__(self):
        return f"Categories: {self.categories}"

    def __repr__(self):
        return f"Categories: {self.categories}"