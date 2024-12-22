import time
from selenium.webdriver.common.by import By

from selenium.common.exceptions import NoSuchElementException
from amazon_connector.types import AmazonOrderItem, AmazonOrderData
from amazon_connector.base_connector import BaseAmazonConnector


class AmazonOrderConnector(BaseAmazonConnector):
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
    import os

    scraper = AmazonOrderConnector(
        username="example@example.com",
        password=os.environ.get("AMAZON_PASSWORD", ""),
    )

    try:
        print("Scraping order info...")
        order_info = scraper.scrape_all_pages(URL)
        print("Scraped Order Info:")
        print(order_info)
        order_info.to_csv("transaction.csv")
    finally:
        scraper.close_driver()
