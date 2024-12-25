from abc import ABC, abstractmethod
from typing import Any
from loguru import logger

from ..monarch_connector.exceptions import CaptchaException, OTPException
from ..amazon_connector.amazon_order_connector import AmazonOrderConnector
from statemachine import StateMachine


class State(ABC):
    def handle(
        self, state_machine: "StateMachine", amazon: AmazonOrderConnector
    ) -> Any:
        try:
            logger.debug(f"State: {self.__class__.__name__}")

            try:
                return self._handle(state_machine=state_machine, amazon=amazon)
            except CaptchaException as e:
                logger.warning(
                    f"Detected captcha in state {self.__class__.__name__}: {e}"
                )
                state_machine.send("redirect_to_captcha", amazon=amazon)
            except OTPException as e:
                logger.warning(f"Detected OTP in state {self.__class__.__name__}: {e}")
                state_machine.send("redirect_to_otp", amazon=amazon)

        except Exception as e:
            logger.error(f"Error in state {self.__class__.__name__}: {e}")
            state_machine.error_occurred()

    @abstractmethod
    def _handle(
        self, state_machine: "StateMachine", amazon: AmazonOrderConnector
    ) -> Any:
        ...


class LoginPageState(State):
    def _handle(self, state_machine: "StateMachine", amazon: AmazonOrderConnector):
        amazon.login()

        state_machine.send("login_success", amazon=amazon)


class CaptchaPageState(State):
    def _handle(self, state_machine: "StateMachine", amazon: AmazonOrderConnector):
        amazon.handle_captcha()

        state_machine.send("captcha_solved", amazon=amazon)


class OTPPageState(State):
    def _handle(self, state_machine: "StateMachine", amazon: AmazonOrderConnector):
        amazon.handle_otp()

        state_machine.send("otp_success", amazon=amazon)


class OrdersPageState(State):
    def _handle(self, state_machine: "StateMachine", amazon: AmazonOrderConnector):
        orders = amazon.get_all_orders()

        state_machine.send("all_orders_scraped_success", amazon=amazon, orders=orders)
