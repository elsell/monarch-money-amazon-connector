from typing import Optional

from ..amazon_connector.types import AmazonOrderData
from ..amazon_connector.amazon_order_connector import AmazonOrderConnector
from .states import LoginPageState, CaptchaPageState, OTPPageState, OrdersPageState
from .states import State as FSMState
from statemachine import State, StateMachine
from loguru import logger
from enum import Enum


class StateName(Enum):
    LOGIN_PAGE = "LoginPage"
    CAPTCHA_PAGE = "CaptchaPage"
    OTP_PAGE = "OTPPage"
    ORDERS_PAGE = "OrdersPage"
    ALL_ORDERS_SCRAPED = "AllOrdersScraped"


class OrderScraperFSM(StateMachine):
    _orders: Optional[AmazonOrderData] = None

    # Define states
    login_page = State(StateName.LOGIN_PAGE.value, initial=True)
    captcha_page = State(StateName.CAPTCHA_PAGE.value)
    otp_page = State(StateName.OTP_PAGE.value)
    orders_page = State(StateName.ORDERS_PAGE.value)
    all_orders_scraped = State(StateName.ALL_ORDERS_SCRAPED.value, final=True)

    # Define transitions (events?)
    redirect_to_captcha = login_page.to(
        captcha_page, cond="captcha_needs_solved and !needs_otp"
    ) | otp_page.to(login_page, cond="needs_otp")
    login_success = (
        login_page.to(
            orders_page,
            cond="!captcha_needs_solved and !needs_to_sign_in and !needs_otp",
        )
        | login_page.to(
            captcha_page,
            cond="captcha_needs_solved and !needs_to_sign_in and !needs_otp",
        )
        | login_page.to(login_page, cond="needs_to_sign_in and !needs_otp")
        | login_page.to(otp_page, cond="needs_otp")
    )
    stay_on_login = login_page.to.itself()

    redirect_to_otp = captcha_page.to(otp_page, cond="needs_otp")
    otp_success = (
        otp_page.to(orders_page, cond="!captcha_needs_solved and !needs_to_sign_in")
        | otp_page.to(captcha_page, cond="captcha_needs_solved")
        | otp_page.to(login_page, cond="needs_to_sign_in")
    )

    captcha_solved = (
        captcha_page.to(
            login_page, cond="!captcha_needs_solved and needs_to_sign_in and !needs_otp"
        )
        | captcha_page.to(
            captcha_page,
            cond="captcha_needs_solved and !needs_to_sign_in and !needs_otp",
        )
        | captcha_page.to(
            orders_page,
            cond="!captcha_needs_solved and !needs_to_sign_in and !needs_otp",
        )
        | captcha_page.to(otp_page, cond="needs_otp")
    )

    redirect_to_login = (
        orders_page.to(login_page, cond="!captcha_needs_solved and needs_to_sign_in")
        | orders_page.to(captcha_page, cond="captcha_needs_solved and !needs_otp")
        | orders_page.to(otp_page, cond="needs_otp")
    )

    stay_on_orders = (
        orders_page.to.itself(cond="!captcha_needs_solved and !needs_to_sign_in")
        | orders_page.to(captcha_page, cond="captcha_needs_solved")
        | orders_page.to(login_page, cond="needs_to_sign_in")
        | orders_page.to(otp_page, cond="needs_otp")
    )

    all_orders_scraped_success = orders_page.to(all_orders_scraped)

    def reset(self):
        self._orders = None
        self.current_state = self.login_page

    def on_exit_state(self, event, state):
        logger.debug(f"Exiting '{state.id}' state from '{event}' event.")

    def on_enter_state(self, event, state):
        logger.debug(f"Entering '{state.id}' state from '{event}' event.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Map states to their respective handler classes
        self.state_handlers: dict[StateName, FSMState] = {
            StateName.LOGIN_PAGE: LoginPageState(),
            StateName.CAPTCHA_PAGE: CaptchaPageState(),
            StateName.ORDERS_PAGE: OrdersPageState(),
            StateName.OTP_PAGE: OTPPageState(),
        }
        self._orders: Optional[AmazonOrderData] = None

    @property
    def orders(self):
        return self._orders

    def captcha_needs_solved(
        self, event, state, amazon: Optional[AmazonOrderConnector] = None
    ):
        if amazon is None:
            return False

        return amazon.on_page_captcha()

    def needs_to_sign_in(self, amazon: Optional[AmazonOrderConnector] = None):
        if amazon is None:
            return False

        return amazon.on_page_login()

    def needs_otp(self, amazon: Optional[AmazonOrderConnector] = None):
        if amazon is None:
            return False

        return amazon.on_page_otp()

    def on_enter_login_page(
        self, event, state, amazon: Optional[AmazonOrderConnector] = None
    ):
        if amazon is None:
            return

        self.state_handlers[StateName.LOGIN_PAGE].handle(
            amazon=amazon, state_machine=self
        )

    def on_enter_captcha_page(
        self, event, state, amazon: Optional[AmazonOrderConnector] = None
    ):
        if amazon is None:
            return

        self.state_handlers[StateName.CAPTCHA_PAGE].handle(
            amazon=amazon, state_machine=self
        )

    def on_enter_orders_page(
        self, event, state, amazon: Optional[AmazonOrderConnector] = None
    ):
        if amazon is None:
            return

        self.state_handlers[StateName.ORDERS_PAGE].handle(
            amazon=amazon, state_machine=self
        )

    def on_enter_otp_page(
        self, event, state, amazon: Optional[AmazonOrderConnector] = None
    ):
        if amazon is None:
            return

        self.state_handlers[StateName.OTP_PAGE].handle(
            amazon=amazon, state_machine=self
        )

    def on_enter_all_orders_scraped(
        self, event, state, amazon: Optional[AmazonOrderConnector] = None, orders=None
    ):
        if amazon is None:
            return
        logger.debug("All orders have been scraped.")
        logger.trace(f"Orders: {orders}")

        self._orders = orders


if __name__ == "__main__":
    from statemachine.contrib.diagram import DotGraphMachine

    graph = DotGraphMachine(OrderScraperFSM)  # type: ignore

    dot = graph().write_png("order_scraper_fsm.png")  # type: ignore
