import time
from monarchmoney import MonarchMoney
import asyncio
from api_types import CategoriesResponse, CategoryDetails, TransactionResponse, Transaction
from csv import DictReader
from connector_types import AmazonOrder, TransactionAmazonMapping
from loguru import logger
from ast import literal_eval

from llm import LLMTool

class MonarchConnector:
    def __init__(self, monarch_money: MonarchMoney):
        self.mm = monarch_money
        self._llm = LLMTool()

    async def get_transactions(self) -> TransactionResponse:
        transactions = await self.mm.get_transactions()
        return TransactionResponse.model_validate(transactions)

    async def get_transactions_need_review(self) -> list[Transaction]:
        transactions = await self.get_transactions()
        transactions_needing_review = [t for t in transactions.allTransactions.results if t.reviewStatus == 'needs_review']
        return transactions_needing_review

    async def match_transactions_to_amazon(self, transaction_csv_file: str) -> list[TransactionAmazonMapping]:
        """Match the transactions that need review to the Amazon orders.
        
        The CSV should have the following columns:
        - order_date
        - total_cost
        - items
        """
        transactions = await self.get_transactions_need_review()

        logger.info(f"Found {len(transactions)} transactions needing review.")

        amazon_orders: list[AmazonOrder] = []

        with open(transaction_csv_file, "r") as fp:
            reader = DictReader(fp)
            for row in reader:
                row['items'] = literal_eval(row['items'])
                amazon_orders.append(AmazonOrder.model_validate(row))

        logger.info(f"Found {len(amazon_orders)} Amazon orders.")

        matches: dict[str, TransactionAmazonMapping] = {}

        skipped_orders: list[Transaction] = []

        for transaction in transactions:
            if transaction.amount > 0:
                skipped_orders.append(transaction)
            else:
                transaction.amount = abs(transaction.amount)

            for order in amazon_orders:

                if transaction.amount == float(order.total_cost.replace("$", "")):
                    if transaction.id not in matches:
                        matches[transaction.id] = TransactionAmazonMapping(transaction=transaction, amazon_orders=[order])
                    else:
                        matches[transaction.id].amazon_orders.append(order)                    

        # Warn on skipped orders
        if skipped_orders:
            logger.warning(f"Skipped {len(skipped_orders)} orders that were: {[o.plaidName for o in skipped_orders]}")

        # Warn on multiple matches
        for transaction_id, mapping in matches.items():
            if len(mapping.amazon_orders) > 1:
                logger.warning(f"Transaction {transaction_id} has multiple matches: {mapping.amazon_orders}")

        return list(matches.values())
    
    async def add_notes_to_amazon_orders(self, matches: list[TransactionAmazonMapping]):
        for match in matches:
            for order in match.amazon_orders:
                item_list = [f"\t- {item}" for item in order.items]
                logger.info(f"Adding note to transaction {match.transaction.id} for Amazon order: {order.order_date}")
                await self.mm.update_transaction(
                    transaction_id=match.transaction.id,
                    notes=f"Date: {order.order_date}\nCost: {order.total_cost}\nItems:\n{'\n'.join(item_list)}"
                )
                time.sleep(1)

    async def get_enabled_categories(self) -> list[CategoryDetails]:
        categories = await self.mm.get_transaction_categories()
        response = CategoriesResponse.model_validate(categories)

        return [c for c in response.categories if c.isDisabled is False]
    
    async def guess_category(self, transaction: TransactionAmazonMapping) -> CategoryDetails:
        """Use the LLM to guess the category of a transaction."""
        categories = await self.get_enabled_categories()
        
        # Provide the available categories as part of the system prompt
        item_list = [f"\t- {item}" for item in transaction.amazon_orders]
        system_prompt = f"Valid available categories: {', '.join([c.name for c in categories])}"
        prompt = f"Guess the category for transaction, only providing one of the valid available categories:\nMerchant: {transaction.transaction.plaidName}\nItems:\n{item_list}"

        print(system_prompt)
        response = self._llm.get_llm_response(system_prompt=system_prompt, prompt=prompt)

        return next(c for c in categories if c.name == response)

async def run():
    mm = MonarchMoney()
    try:
        mm.load_session()
    except FileNotFoundError:
        await mm.interactive_login()

    m = MonarchConnector(monarch_money=mm)

    matches = await m.match_transactions_to_amazon("../test_john.csv")

    await m.add_notes_to_amazon_orders(matches)



if __name__ == "__main__":
    asyncio.run(run())

