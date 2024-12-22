from ..config.types import AmazonAccount, Config
from loguru import logger
from ..amazon_connector.amazon_order_connector import AmazonOrderConnector
from ..monarch_connector.monarch import MonarchConnector
from monarchmoney import MonarchMoney


class MonarchMoneyAmazonConnectorCLI:
    def __init__(self, config: Config):
        self.config = config

    async def _get_monarch_money(self) -> MonarchMoney:
        self._mm = MonarchMoney()
        try:
            self._mm.load_session()
        except FileNotFoundError:
            await self._mm.login(
                email=self.config.monarch_account.email,
                password=self.config.monarch_account.password,
            )

        return self._mm

    async def _annotate_single_account(
        self, account: AmazonAccount, monarch_connector: MonarchConnector
    ):
        logger.info(f"Annotating transactions found in Amazon Account: {account.email}")

        connector = AmazonOrderConnector(
            username=account.email, password=account.password
        )

        orders = connector.scrape_all_pages()

        logger.debug(
            f"Found {len(orders.orders)} orders for Amazon account: {account.email}"
        )

        logger.debug(
            f"Matching transactions to Amazon orders for Amazon account: {account.email}"
        )
        transaction_mapping = await monarch_connector.match_transactions_to_amazon(
            orders
        )

        logger.debug(
            f"Adding notes to Amazon orders for Amazon account: {account.email}"
        )
        await monarch_connector.add_notes_to_amazon_orders(matches=transaction_mapping)

    async def annotate_transactions(self):
        logger.info(
            f"Annotating transactions across {len(self.config.amazon_accounts)} Amazon accounts."
        )

        monarch_connector = MonarchConnector(
            monarch_money=await self._get_monarch_money()
        )

        for account in self.config.amazon_accounts:
            await self._annotate_single_account(
                account=account, monarch_connector=monarch_connector
            )
