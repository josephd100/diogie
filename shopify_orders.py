import sys 
import os 
import csv
import shopify
from dotenv import load_dotenv
load_dotenv()

def get_last_order_name():
    with open("automated_orders.csv", "r", newline = '') as f:
        lines = f.readlines()
    if len(lines) >= 2:     
        last_order = int(lines[-1].split(",", 1)[0]) 
    else:
        last_order = None 
    return last_order, len(lines) >= 1

last_order, has_header = get_last_order_name() 
print(last_order)
# sys.exit()

API_KEY = os.getenv("API_KEY")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
API_ACCESS_TOKEN = os.getenv("API_ACCESS_TOKEN")
SHOP_NAME = os.getenv("SHOP_NAME")

shopify.Session.setup(api_key=API_KEY, secret=API_SECRET_KEY)
shop_url = f"{SHOP_NAME}.myshopify.com"
api_version = '2024-07'
private_app_password = API_ACCESS_TOKEN

session = shopify.Session(shop_url, api_version, token=private_app_password)
shopify.ShopifyResource.activate_session(session)
orders = shopify.Order.find(limit="250")
print(orders)

with open("automated_orders.csv", "a", newline="") as f:
    field_names = ["order_name", "order_id", "sku", "product_name", "quantity", "ordered_date", "shipping_city", "shipping_state"]
    writer = csv.DictWriter(f, fieldnames = field_names)
    if has_header == False:
        writer.writeheader()
    for order in reversed(orders):
        order = order.to_dict()
        order_data = {
            "order_name": int(order["name"][1 : ]),
            "order_id": order["id"],
            "ordered_date": order["created_at"],
            "shipping_city": order["shipping_address"]["city"],
            "shipping_state": order["shipping_address"]["province_code"],
        }
        if order_data["order_name"] > last_order:
            for line_item in order['line_items']:
                rowdict = {
                    "product_name": line_item['name'],
                    "sku": line_item['sku'],
                    "quantity": line_item['quantity'],
                }
                rowdict.update(order_data)
                writer.writerow(rowdict)
shopify.ShopifyResource.clear_session()
