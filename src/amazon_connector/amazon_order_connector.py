import time
from selenium.webdriver.common.by import By

from selenium.common.exceptions import NoSuchElementException
from .types import AmazonOrderItem, AmazonOrderData
from .base_connector import BaseAmazonConnector
from loguru import logger


class AmazonOrderConnector(BaseAmazonConnector):
    _ORDERS_PER_PAGE = 10

    def get_all_orders(self) -> AmazonOrderData:
        """
        Get all orders for the logged in user.

        TODO: By default, this method will only return 3 months of order history.
            This is due to Amazon defaulting to a 3 month view of orders. The only other
            views are by year, which may cause boundary conditions if we are not careful.

            A possible solution would be allowing the user to specify a max orders, or time
            frame to retrieve. Then, we could begin at the current year and walk backwards
            until we have enough orders. This would handle the boundary condition that occurs
            when we cross a year boundary.

        Returns:
            AmazonOrderData: A list of AmazonOrderItem objects
        """
        count_orders_on_page = None
        page = 0

        account = self._get_logged_in_user_email()

        all_orders = AmazonOrderData(orders=[], account_email=account)

        while count_orders_on_page is None or count_orders_on_page > 0:
            page_url = self._url_orders + f"?&startIndex={page * self._ORDERS_PER_PAGE}"

            orders_on_page = self._scrape_order_info(url=page_url)

            count_orders_on_page = len(orders_on_page.orders)

            logger.trace(
                f"Found {count_orders_on_page} orders on page {page} for {account}"
            )

            all_orders.orders.extend(orders_on_page.orders)

            page = page + 1

        return all_orders

    def _scrape_order_info(self, url: str) -> AmazonOrderData:
        logger.trace(f"Scraping order info from {url}")
        self._navigate_safe(url)

        time.sleep(3)  # Wait for the page to load

        # Check if we're on the login page, not the orders page
        if "signin" in self.driver.current_url:
            self.login(self._username, self._password)
            self._navigate_safe(url)
            time.sleep(3)

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
            logger.error(f"An error occurred: {e}")

        return orders

    def close_driver(self):
        self.driver.quit()


if __name__ == "__main__":
    URL = "https://www.amazon.com/your-orders/orders"

    print("Starting scraper...")
    import os

    scraper = AmazonOrderConnector(
        username="example@example.com",
        password=os.environ.get("AMAZON_PASSWORD", ""),
    )

    try:
        print("Scraping order info...")
        order_info = scraper.get_all_orders()
        print("Scraped Order Info:")
        print(order_info)
        order_info.to_csv("transaction.csv")
    finally:
        scraper.close_driver()
