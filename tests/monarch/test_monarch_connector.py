import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List
from src.config.types import MonarchAccount, TransactionFilters
from src.monarch_connector.monarch import MonarchConnector, Transaction, Config
from src.monarch_connector.api_types import (
    AllTransactions,
    Category,
    Merchant,
    TransactionResponse,
    TransactionTag,
)


class TestGetTransactionsNeedReview:
    """
    Test suite for the `get_transactions_need_review` method.
    """

    # Arrange: Set up mock data for transactions
    _mock_transactions = [
        Transaction(
            id="1",
            amount=100.0,
            pending=False,
            date="2024-01-01",
            hideFromReports=False,
            plaidName="Grocery Store",
            notes=None,
            isRecurring=False,
            reviewStatus="needs_review",
            needsReview=True,
            attachments=[],
            isSplitTransaction=False,
            createdAt="2024-01-01",
            updatedAt="2024-01-01",
            category=Category(id="", name=""),
            merchant=Merchant(id="m1", name="Grocery Store", transactionsCount=0),
            account={},
            tags=[TransactionTag(id="tag1", name="Important", color="", order=-1)],
        ),
        Transaction(
            id="2",
            amount=200.0,
            pending=False,
            date="2024-01-02",
            hideFromReports=False,
            plaidName="Coffee Shop",
            notes=None,
            isRecurring=False,
            reviewStatus="needs_review",
            needsReview=True,
            attachments=[],
            isSplitTransaction=False,
            createdAt="2024-01-02",
            updatedAt="2024-01-02",
            category=Category(id="", name=""),
            merchant=Merchant(id="m2", name="Coffee Shop", transactionsCount=0),
            account={},
            tags=[],
        ),
        Transaction(
            id="3",
            amount=150.0,
            pending=False,
            date="2024-01-03",
            hideFromReports=False,
            plaidName="Bookstore",
            notes=None,
            isRecurring=False,
            reviewStatus="reviewed",
            needsReview=False,
            attachments=[],
            isSplitTransaction=False,
            createdAt="2024-01-03",
            updatedAt="2024-01-03",
            category=Category(id="", name=""),
            merchant=Merchant(id="m3", name="Bookstore", transactionsCount=0),
            account={},
            tags=[],
        ),
        Transaction(
            id="4",
            amount=29.0,
            pending=False,
            date="2024-01-03",
            hideFromReports=False,
            plaidName="Market",
            notes=None,
            isRecurring=False,
            reviewStatus="needs_review",
            needsReview=False,
            attachments=[],
            isSplitTransaction=False,
            createdAt="2024-01-03",
            updatedAt="2024-01-03",
            category=Category(id="", name=""),
            merchant=Merchant(id="m4", name="Market", transactionsCount=0),
            account={},
            tags=[],
        ),
    ]

    @pytest.mark.asyncio
    async def test_cases(self):
        """
        Test the `get_transactions_need_review` method with multiple configurations.
        """

        # Mock the `get_transactions` method to return the mock data
        mock_mm = MagicMock()

        transactions = self._mock_transactions

        async def x(limit):
            return TransactionResponse(
                allTransactions=AllTransactions(results=transactions)
            )

        mock_mm.get_transactions = x

        # Define test configurations
        test_configs = [
            # Case 1: Filter by merchant name "Market"
            Config(
                amazon_accounts=[],
                monarch_account=MonarchAccount(email="", password=""),
                transaction_filters=[
                    TransactionFilters(
                        merchant_name="maRkeT",
                        ignore_case=True,
                        search_by_contains=False,
                    )
                ],
            ),
            # Case 2: No filters applied
            Config(
                amazon_accounts=[],
                monarch_account=MonarchAccount(email="", password=""),
                transaction_filters=[],
            ),
            # Case 3: Filter by merchant name "Grocery" (partial match, ignore case enabled)
            Config(
                amazon_accounts=[],
                monarch_account=MonarchAccount(email="", password=""),
                transaction_filters=[
                    TransactionFilters(
                        merchant_name="grocery",
                        ignore_case=True,
                        search_by_contains=True,
                    )
                ],
            ),
        ]

        # Mock the `_get_mmac_tag_id` method
        tag_id = "tag1"
        mock_connector = MonarchConnector(
            mock_mm, test_configs[0]
        )  # Using first config initially
        mock_connector._get_mmac_tag_id = AsyncMock(return_value=tag_id)

        # Act & Assert: Evaluate each configuration scenario
        expected_results = [
            # Case 1: Only "Market" transaction matches the filter
            [transactions[3]],
            # Case 2: No filters, all transactions with needsReview=True and no mmac tag should be returned (Just coffee and market)
            [transactions[1], transactions[3]],
            # Case 3: Only "Grocery Store" matches the partial match filter, but it is tagged. So no results.
            [],
        ]

        for i, config in enumerate(test_configs):
            mock_connector._config = config  # Update config for the test case
            filtered_transactions: List[
                Transaction
            ] = await mock_connector.get_transactions_need_review()

            # Assertions
            assert (
                len(filtered_transactions) == len(expected_results[i])
            ), f"Failed Test Case idx={i}. Actual != Expected ({filtered_transactions} != {expected_results[i]})"
            for filtered, expected in zip(filtered_transactions, expected_results[i]):
                assert filtered.id == expected.id
                assert filtered.merchant.name == expected.merchant.name
