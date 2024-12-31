from abc import ABC
from typing import Literal, Optional
from selenium import webdriver
from selenium.common.exceptions import InvalidCookieDomainException
from selenium.webdriver.common.by import By
import pickle
import time
from selenium.common.exceptions import NoSuchElementException
from pathlib import Path
from loguru import logger

from ..monarch_connector.exceptions import CaptchaException

from ..captcha_solver.abstract_captcha_solver import AbstractCaptchaSolver


class BaseAmazonConnector(ABC):
    _AMAZON_URL = "https://www.amazon.com"

    def __init__(
        self,
        username: str,
        password: str,
        browser: Literal["firefox"] | Literal["chrome"] = "chrome",
        headless: bool = True,
        pause_between_navigation: bool = False,
        captcha_solver: Optional[AbstractCaptchaSolver] = None,
    ):
        self._username = username
        self._password = password

        self._headless = headless

        self._pause_between_navigation = pause_between_navigation

        self._captcha_solver = captcha_solver

        self._browser_choice = browser

        self._init_config_dir()

        self.driver = self._initialize_driver()

        self.load_cookies()

    def __del__(self):
        self.driver.quit()

    @property
    def _config_directory(self) -> Path:
        return Path(".mmac")

    @property
    def _tmp_directory(self) -> Path:
        return self._config_directory / "tmp"

    @property
    def _firefox_profile_directory(self) -> Path:
        return self._config_directory / "firefox-profile" / "default"

    @property
    def _url_orders(self) -> str:
        return f"{self._AMAZON_URL}/your-orders/orders"

    @property
    def _url_account_management(self) -> str:
        return f"{self._AMAZON_URL}/ax/account/manage"

    @property
    def _url_signin(self) -> str:
        return f"{self._AMAZON_URL}/ap/signin?openid.assoc_handle=usflex&openid.pape.max_auth_age=900&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"

    @property
    def _cookies_file(self) -> Path:
        return self._config_directory / "cookies.pkl"

    def _solve_captcha(self, image_url: str | None) -> str:
        if self._captcha_solver is None or image_url is None:
            if image_url is None:
                logger.warning(
                    "Could not determine captcha image url. Please solve the captcha manually."
                )
            else:
                logger.warning(
                    "No captcha solver provided. Please solve the captcha manually. Image: {}",
                    image_url,
                )
            solved_captcha = input("Please enter the solved captcha: ")
            return solved_captcha

        logger.info("Solving captcha with LLM.")
        solved_captcha = self._captcha_solver.solve_captcha_from_url(
            image_url=image_url
        )
        logger.info(f"Solved captcha: {solved_captcha}")
        return solved_captcha

    def _init_config_dir(self):
        logger.debug(f"Initializing config directory @ {self._config_directory}")
        Path(self._firefox_profile_directory).mkdir(parents=True, exist_ok=True)

    def _get_firefox_driver(self):
        from selenium.webdriver.firefox.service import Service
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
        from webdriver_manager.firefox import GeckoDriverManager

        options = Options()
        if self._headless:
            options.add_argument("-headless")
        profile = FirefoxProfile(profile_directory=self._firefox_profile_directory)
        options.profile = profile

        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)

        return driver

    def _get_chrome_driver(self):
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        if self._headless:
            options.add_argument("--headless=new")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        return driver

    def _initialize_driver(self):
        if self._browser_choice == "firefox":
            driver = self._get_firefox_driver()
        elif self._browser_choice == "chrome":
            driver = self._get_chrome_driver()
        else:
            raise Exception(f"Unsupported browser: {self._browser_choice}")

        return driver

    def on_page_captcha(self):
        return "captcha" in self.driver.page_source.lower()

    def handle_captcha(self):
        try:
            while self.on_page_captcha():
                page_source = self.driver.page_source

                # Check if "captcha" appears in the page source. This appears
                # to be a reliable way to detect if a captcha is present.
                if "captcha" not in page_source.lower():
                    return

                captcha_img = self.driver.find_element(By.TAG_NAME, "img")
                captcha_src = captcha_img.get_attribute("src")

                logger.trace(f"Found captcha image: {captcha_src}")

                if not captcha_src:
                    logger.warning("Failed to find captcha image url.")

                solved_captcha = self._solve_captcha(image_url=captcha_src)

                captcha_input = self.driver.find_element(
                    By.XPATH, "//input[@type='text']"
                )
                captcha_input.send_keys(solved_captcha)

                continue_button = self.driver.find_element(
                    By.XPATH, "//button[@type='submit'] | //input[@type='submit']"
                )

                if self._pause_between_navigation:
                    input("Pausing after solving captcha. Press Enter to continue...")

                continue_button.click()

                time.sleep(3)  # Wait for the page to load
        except NoSuchElementException:
            logger.trace("No captcha/submit found.")
            pass

    def on_page_login(self):
        return "signin" in self.driver.current_url

    def _navigate_safe(self, url: str, calling_from_login: bool = False):
        """Navigate to a URL, throwing exceptions if the resulting page is not the expected page."""

        logger.trace(f"Attempting to navigate to {url}")
        if self._pause_between_navigation:
            input("Pausing before navigation. Press Enter to continue...")

        self.driver.get(url)

        if self.on_page_captcha():
            raise CaptchaException("Captcha detected. Cannot navigate.")

        if url not in self.driver.current_url:
            logger.warning(
                f"Failed to navigate to {url}. Instead, navigated to {self.driver.current_url}"
            )
            # raise Exception(
            #     f"Failed to navigate to {url}. Instead, navigated to {self.driver.current_url}"
            # )

    def load_cookies(self):
        try:
            cookies = pickle.load(open(self._cookies_file, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
        except FileNotFoundError:
            pass
        except InvalidCookieDomainException:
            logger.warning("Failed to load cookies. Invalid domain.")
            # Remove the cookies file
            self._cookies_file.unlink()

    def on_page_otp(self):
        return "auth-mfa-otpcode" in self.driver.page_source

    def handle_otp(self):
        try:
            otp_input = self.driver.find_element(By.ID, "auth-mfa-otpcode")
            otp_continue_button = self.driver.find_element(By.ID, "auth-signin-button")
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
        time.sleep(3)  # Wait for the page to load

    def _get_logged_in_user_email(self):
        return self._username

    def logout(self):
        signout_button_id = "nav-item-signout"
        try:
            signout_button = self.driver.find_element(By.ID, signout_button_id)
            signout_button.click()
        except NoSuchElementException:
            logger.trace(f"Could not find signout button with ID: {signout_button_id}")

    def _login(self, email: str, password: str):
        self.logout()

        self._navigate_safe(self._url_signin, calling_from_login=True)

        try:
            email_input = self.driver.find_element(By.ID, "ap_email")
            email_input.send_keys(email)
            logger.trace("Email entered.")

            continue_button = self.driver.find_element(By.ID, "continue")
            continue_button.click()
            time.sleep(3)  # Wait for the page to load
        except NoSuchElementException:
            logger.warning("Failed to find email input field. Trying to login anyway.")
            pass

        if self.on_page_captcha():
            raise CaptchaException("Captcha detected. Cannot navigate.")

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
            logger.warning(
                "Failed to find password input field. Trying to login anyway."
            )
            pass

    def login(self):
        self._login(email=self._username, password=self._password)
