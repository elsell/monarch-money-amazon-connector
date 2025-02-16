from ..config.types import AmazonAccount, Config
from loguru import logger
from ..amazon_connector.amazon_order_connector import AmazonOrderConnector
from ..monarch_connector.monarch import MonarchConnector
from monarchmoney import MonarchMoney
from ..captcha_solver.llm_captcha_solver import LLMCaptchaSolver
from ..fsm.state_machine_implementation import OrderScraperFSM


class MonarchMoneyAmazonConnectorCLI:
    def __init__(self, config: Config):
        self._config = config

        self._captcha_solver = None

        self._fsm = OrderScraperFSM()

        if self._config.llm.enable_llm_captcha_solver:
            self._captcha_solver = LLMCaptchaSolver(
                openai_api_key=self._config.llm.api_key,
                model_name=self._config.llm.llm_model_name,
                base_url=self._config.llm.base_url,
                project=self._config.llm.project,
                organization=self._config.llm.organization,
            )

    async def _get_monarch_money(self) -> MonarchMoney:
        self._mm = MonarchMoney()
        try:
            self._mm.load_session()
            logger.info("Monarch Money session found. Using existing session.")
        except FileNotFoundError:
            logger.info("No Monarch Money session found. Logging in.")
            logger.debug(
                f"Logging in with email: {self._config.monarch_account.email}, password: '{self._config.monarch_account.password}'"
            )
            await self._mm.login(
                email=self._config.monarch_account.email,
                password=self._config.monarch_account.password,
            )

        return self._mm

    async def _annotate_single_account(
        self, account: AmazonAccount, monarch_connector: MonarchConnector
    ):
        logger.info(f"Annotating transactions found in Amazon Account: {account.email}")

        connector = AmazonOrderConnector(
            username=account.email,
            password=account.password,
            headless=self._config.headless,
            pause_between_navigation=self._config.debug.pause_between_navigation,
            captcha_solver=self._captcha_solver,
            searchFilter=self._config.amazon_filter,
        )

        logger.info("Retrieving Amazon orders.")

        if self._fsm.current_state.id == self._fsm.all_orders_scraped.id:
            self._fsm.reset()

        self._fsm.send("stay_on_login", amazon=connector)

        if self._fsm.orders is None:
            logger.error(
                f"Failed to retrieve orders for Amazon account: {account.email}"
            )
            return

        orders = self._fsm.orders

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
            f"Annotating transactions across {len(self._config.amazon_accounts)} Amazon accounts."
        )

        monarch_connector = MonarchConnector(
            monarch_money=await self._get_monarch_money(), config=self._config
        )

        for account in self._config.amazon_accounts:
            await self._annotate_single_account(
                account=account, monarch_connector=monarch_connector
            )
