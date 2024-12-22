from abc import ABC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from webdriver_manager.firefox import GeckoDriverManager
import pickle
import time
from selenium.common.exceptions import NoSuchElementException
from pathlib import Path
from loguru import logger


class BaseAmazonConnector(ABC):
    _AMAZON_URL = "https://www.amazon.com"

    def __init__(self, username: str, password: str, auto_login: bool = True):
        self._username = username
        self._password = password

        self._init_config_dir()

        self.driver = self._initialize_driver()

        self.driver.get(self._AMAZON_URL)

        self.load_cookies()

        if auto_login:
            self.login(email=username, password=password)
        else:
            input("Please sign in, then press Enter to continue...")

    @property
    def _config_directory(self) -> Path:
        return Path(".mmac")

    @property
    def _firefox_profile_directory(self) -> Path:
        return self._config_directory / "firefox-profile" / "default"

    @property
    def _cookies_file(self) -> Path:
        return self._config_directory / "cookies.pkl"

    def _init_config_dir(self):
        logger.debug(f"Initializing config directory @ {self._config_directory}")
        Path(self._firefox_profile_directory).mkdir(parents=True, exist_ok=True)

    def _initialize_driver(self):
        options = Options()
        profile = FirefoxProfile(profile_directory=self._firefox_profile_directory)
        options.profile = profile

        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)

        return driver

    def load_cookies(self):
        try:
            cookies = pickle.load(open(self._cookies_file, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
        except FileNotFoundError:
            pass

    def _handle_otp(self):
        code_correct = False

        while not code_correct:
            try:
                otp_input = self.driver.find_element(By.ID, "auth-mfa-otpcode")
                otp_continue_button = self.driver.find_element(
                    By.ID, "auth-signin-button"
                )
                remember_device_button = self.driver.find_element(
                    By.ID, "auth-mfa-remember-device"
                )
            except NoSuchElementException:
                return

            logger.info("OTP Code required.")

            otp_code = input("Please enter a OTP Code: ")

            otp_input.send_keys(otp_code)
            remember_device_button.click()
            time.sleep(1)
            otp_continue_button.click()

            auth_error_message_box = self.driver.find_element(
                By.ID, "auth-error-message-box"
            )
            if auth_error_message_box:
                logger.error("OTP Code was incorrect. Please try again.")
            else:
                logger.info("OTP Code was correct.")
                code_correct = True

    def login(self, email: str, password: str):
        # We're already on the login page
        try:
            email_input = self.driver.find_element(By.ID, "ap_email")
            email_input.send_keys(email)
            logger.trace("Email entered.")

            continue_button = self.driver.find_element(By.ID, "continue")
            continue_button.click()
            time.sleep(6)  # Wait for the page to load
        except NoSuchElementException:
            pass

        try:
            password_input = self.driver.find_element(By.ID, "ap_password")
            password_input.send_keys(password)
            logger.trace("Password entered.")

            sign_in_button = self.driver.find_element(By.ID, "signInSubmit")
            sign_in_button.click()

            time.sleep(3)  # Wait for the page to load

            logger.trace(f"Saving cookies to {self._cookies_file}")
            pickle.dump(self.driver.get_cookies(), open(self._cookies_file, "wb"))
        except NoSuchElementException:
            pass

        # Check for TOTP page
        try:
            self._handle_otp()

        except NoSuchElementException:
            pass
