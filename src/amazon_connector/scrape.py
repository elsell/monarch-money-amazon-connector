import pickle
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

from selenium.common.exceptions import NoSuchElementException
from amazon_connector.types import AmazonOrderItem, AmazonOrderData


class AmazonConnector:
    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password

        self.driver = self.initialize_driver()

        self.driver.get("https://www.amazon.com")

        input("Please log in, then press Enter to continue...")

        self.load_cookies()

    def initialize_driver(self):
        options = Options()
        profile = FirefoxProfile(
            profile_directory="/home/john/snap/firefox/common/.mozilla/firefox/7oju93b7.default-release"
        )
        options.profile = profile

        service = Service("/snap/bin/firefox.geckodriver")
        driver = webdriver.Firefox(service=service, options=options)
        return driver

    def load_cookies(self):
        try:
            cookies = pickle.load(open("cookies.pkl", "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
        except FileNotFoundError:
            pass

    def login(self, email, password):
        # We're already on the login page
        try:
            email_input = self.driver.find_element(By.ID, "ap_email")
            email_input.send_keys(email)
            continue_button = self.driver.find_element(By.ID, "continue")
            continue_button.click()
            time.sleep(6)  # Wait for the page to load
        except NoSuchElementException:
            pass

        try:
            password_input = self.driver.find_element(By.ID, "ap_password")
            password_input.send_keys(password)

            sign_in_button = self.driver.find_element(By.ID, "signInSubmit")
            sign_in_button.click()

            pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))

            time.sleep(3)  # Wait for the page to load
        except NoSuchElementException:
            pass

    def scrape_all_pages(self, base_url: str) -> AmazonOrderData:
        count_orders_on_page = None
        page = 0

        all_orders = AmazonOrderData(orders=[])

        while count_orders_on_page is None or count_orders_on_page > 0:
            page_url = base_url + f"?&startIndex={page * 10}"

            orders_on_page = self.scrape_order_info(url=page_url)

            count_orders_on_page = len(orders_on_page.orders)

            all_orders.orders.extend(orders_on_page.orders)

            page = page + 1

        return all_orders

    def scrape_order_info(self, url) -> AmazonOrderData:
        self.driver.get(url)

        time.sleep(3)  # Wait for the page to load

        # Check if we're on the login page, not the orders page
        if "signin" in self.driver.current_url:
            self.login(self._username, self._password)

        orders = AmazonOrderData(orders=[])

        try:
            all_cards = self.driver.find_elements(By.CSS_SELECTOR, ".order-card")
            for order_card in all_cards:
                order_info: AmazonOrderItem = AmazonOrderItem()

                order_date = order_card.find_elements(By.CSS_SELECTOR, ".a-size-base")[
                    0
                ].text
                total_cost = order_card.find_elements(By.CSS_SELECTOR, ".a-size-base")[
                    1
                ].text
                items = order_card.find_elements(
                    By.CSS_SELECTOR, ".yohtmlc-product-title"
                )
                order_info.order_date = order_date
                order_info.total_cost = total_cost
                order_info.items = [item.text for item in items]

                orders.orders.append(order_info)

        except NoSuchElementException as e:
            print(f"An error occurred: {e}")

        return orders

    def close_driver(self):
        self.driver.quit()


if __name__ == "__main__":
    # TODO: This only will show 3 months of order history. It would
    # be good to give users a way to specify a time filter.
    URL = "https://www.amazon.com/your-orders/orders"

    print("Starting scraper...")

    scraper = AmazonConnector(username="", password="")

    try:
        print("Scraping order info...")
        order_info = scraper.scrape_all_pages(URL)
        print("Scraped Order Info:")
        print(order_info)
        order_info.to_csv("transaction.csv")
    finally:
        scraper.close_driver()
