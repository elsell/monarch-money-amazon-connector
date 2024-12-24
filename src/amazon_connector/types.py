from typing import Optional
import csv
import json
from pydantic import BaseModel


class AmazonOrderItem(BaseModel):
    order_date: Optional[str] = None
    total_cost: Optional[str] = None
    items: Optional[list[str]] = None


class AmazonOrderData(BaseModel):
    account_email: Optional[str] = None
    orders: list[AmazonOrderItem]

    def to_csv(self, filename: str):
        fieldnames = list(AmazonOrderItem.model_json_schema()["properties"].keys())
        fieldnames.append("account_email")
        
        with open(filename, "w") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            writer.writeheader()
            for order in self.orders:
                row = json.loads(order.model_dump_json())
                row['account_email'] = self.account_email
                writer.writerow(row)