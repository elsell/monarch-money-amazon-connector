import time
from monarchmoney import MonarchMoney

from .exceptions import TagAlreadyExistsException

from ..config.types import Config
from .api_types import (
    CategoriesResponse,
    CategoryDetails,
    CreateTransactionTagResponse,
    TransactionResponse,
    Transaction,
    TransactionTag,
    TransactionTagResponse,
)
from .connector_types import AmazonOrder, TransactionAmazonMapping
from loguru import logger

from ..amazon_connector.types import AmazonOrderData


class MonarchConnector:
    def __init__(self, monarch_money: MonarchMoney, config: Config):
        self.mm = monarch_money

        self._config = config

    async def get_transactions(self) -> TransactionResponse:
        transactions = await self.mm.get_transactions(limit=1000)
        return TransactionResponse.model_validate(transactions)

    async def get_transactions_need_review(self) -> list[Transaction]:
        """Gets the transactions that need review, filtering out those that have the MMAC tag and don't ."""

        mmac_tag_id = await self._get_mmac_tag_id()

        logger.trace("MMAC Tag ID set to '{}'", mmac_tag_id)

        transaction_filters = self._config.transaction_filters

        transactions = await self.get_transactions()
        transactions_needing_review = [
            t
            for t in transactions.allTransactions.results
            if t.reviewStatus == "needs_review"
            and (mmac_tag_id not in [tag.id for tag in t.tags])
        ]

        logger.trace(
            "Found {} transaction(s) that need review and don't have mmac tag: {}",
            len(transactions_needing_review),
            transactions_needing_review,
        )

        filtered_transactions: list[Transaction] = []

        if len(transaction_filters) == 0:
            filtered_transactions = transactions_needing_review
        else:
            for transaction in transactions_needing_review:
                logger.trace("Checking transaction: {}", transaction)
                for filter in transaction_filters:
                    merchant_name = transaction.merchant.name

                    if filter.ignore_case:
                        merchant_name = merchant_name.lower()
                        filter.merchant_name = filter.merchant_name.lower()

                    logger.trace(
                        "Comparing '{}' to '{}'...", merchant_name, filter.merchant_name
                    )

                    passes_filter = False

                    if filter.search_by_contains:
                        passes_filter = filter.merchant_name in merchant_name
                    else:
                        passes_filter = filter.merchant_name == merchant_name

                    if passes_filter:
                        logger.trace("Transaction {} passes filter.", transaction)
                        filtered_transactions.append(transaction)
                        break
                    else:
                        logger.trace("Transaction {} fails filter.", transaction)

        return filtered_transactions

    async def match_transactions_to_amazon(
        self, amazon_orders: AmazonOrderData
    ) -> list[TransactionAmazonMapping]:
        """Match the transactions that need review to the Amazon orders.

        The CSV should have the following columns:
        - order_date
        - total_cost
        - items
        """
        transactions = await self.get_transactions_need_review()

        validated_orders = [
            AmazonOrder.model_validate(o.model_dump()) for o in amazon_orders.orders
        ]

        for order in validated_orders:
            order.account_email = amazon_orders.account_email

        logger.info(f"Found {len(transactions)} transactions needing review.")

        logger.info(f"Found {len(validated_orders)} Amazon orders.")

        matches: dict[str, TransactionAmazonMapping] = {}

        skipped_orders: list[Transaction] = []

        for transaction in transactions:
            if transaction.amount > 0:
                skipped_orders.append(transaction)
            else:
                transaction.amount = abs(transaction.amount)

            for order in validated_orders:
                if transaction.amount == float(order.total_cost.replace("$", "")):
                    if transaction.id not in matches:
                        matches[transaction.id] = TransactionAmazonMapping(
                            transaction=transaction, amazon_orders=[order]
                        )
                    else:
                        matches[transaction.id].amazon_orders.append(order)

        # Warn on skipped orders
        if skipped_orders:
            logger.warning(
                f"Skipped {len(skipped_orders)} orders that were: {[o.plaidName for o in skipped_orders]}"
            )

        # Warn on multiple matches
        for transaction_id, mapping in matches.items():
            if len(mapping.amazon_orders) > 1:
                logger.warning(
                    f"Transaction {transaction_id} has multiple matches: {mapping.amazon_orders}"
                )

        logger.info(f"Found {len(matches)} transactions to annotate.")

        return list(matches.values())

    async def _get_transaction_tags(self) -> list[TransactionTag]:
        all_tags = TransactionTagResponse.model_validate(
            await self.mm.get_transaction_tags()
        )

        logger.debug(f"Found {len(all_tags.householdTransactionTags)} tags.")

        return all_tags.householdTransactionTags

    async def _create_transaction_tag(
        self, tag_name: str, tag_color: str
    ) -> TransactionTag:
        """Create a tag in Monarch Money.

        Args:
            tag_name (str): The name of the tag.
            tag_color (str): The color of the tag.

        Returns:
            TransactionTag: The created tag.

        Raises:
            TagAlreadyExistsException: If the tag already exists.
        """
        logger.info(f"Creating tag '{tag_name}' in Monarch Money.")

        tag = CreateTransactionTagResponse.model_validate(
            await self.mm.create_transaction_tag(name=tag_name, color=tag_color)
        )

        if tag.createTransactionTag.tag is None and tag.createTransactionTag.errors:
            logger.trace(
                f"Failed to create tag: {tag.createTransactionTag.errors.message}"
            )
            raise TagAlreadyExistsException(
                f"Error creating tag '{tag_name}'. It already exists."
            )
        elif tag.createTransactionTag.tag is None:
            logger.error(
                f"Failed to create tag {tag_name}. Unexpected missing tag data."
            )
            raise Exception("Failed to create tag.")

        return tag.createTransactionTag.tag

    async def _get_tag(self, name: str, color: str) -> str:
        """Gets a MonarchMoney tag, creating it if it doesn't already exist.

        Returns:
            str: The tag ID.
        """
        all_tags = await self._get_transaction_tags()

        tag_names = set(list(t.name for t in all_tags))

        # Tag doesn't exist
        if name not in tag_names:
            logger.info(f"Creating tag '{name}' in Monarch Money.")

            tag = await self._create_transaction_tag(
                tag_name=name,
                tag_color=color,
            )

        # Tag Does Exist
        else:
            tag = next(t for t in all_tags if t.name == name)

        return tag.id

    async def _get_mmac_tag_id(self) -> str:
        """Gets the MMAC tag, creating it if it doesn't already exist.

        Returns:
            str: The tag ID.
        """
        return await self._get_tag(
            name=self._config.transaction_tag.name,
            color=self._config.transaction_tag.color,
        )

    async def add_notes_to_amazon_orders(self, matches: list[TransactionAmazonMapping]):
        """
        This method also adds a tag to the Monarch Transaction, which is used
        to prevent overwriting the note on subsequent runs. This tag can be configured
        using the config file or environment variables.
        """
        tag_id = await self._get_mmac_tag_id()

        for match in matches:
            for order in match.amazon_orders:
                item_list = [f"\t- {item}" for item in order.items]
                logger.info(
                    f"Adding note to transaction {match.transaction.id} for Amazon order: {order.order_date}"
                )

                # Add Note
                await self.mm.update_transaction(
                    transaction_id=match.transaction.id,
                    notes=f"Date: {order.order_date}\nAccount: {order.account_email}\nItems:\n{'\n'.join(item_list)}",
                )

                # Add Tag
                previous_tag_ids = [t.id for t in match.transaction.tags]
                previous_tag_ids.append(tag_id)
                new_tags = list(set(previous_tag_ids))

                if self._config.amazon_account_tag.enabled and order.account_email:
                    tag_name = (
                        f"{self._config.amazon_account_tag.prefix}{order.account_email}"
                    )
                    account_tag = await self._get_tag(
                        name=tag_name,
                        color=self._config.amazon_account_tag.color,
                    )
                    new_tags.append(account_tag)

                await self.mm.set_transaction_tags(
                    transaction_id=match.transaction.id, tag_ids=new_tags
                )
                time.sleep(1)

    async def get_enabled_categories(self) -> list[CategoryDetails]:
        categories = await self.mm.get_transaction_categories()
        response = CategoriesResponse.model_validate(categories)

        return [c for c in response.categories if c.isDisabled is False]
