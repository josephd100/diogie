import os
import requests
import pandas as pd
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Load environment variables
load_dotenv(dotenv_path="api_keys.env")

# Google Sheet setup
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "service_account.json")
SHEET_NAME = "Diogie_Orders"

# Setup API Client 
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(credentials)

# Open the Google Sheet
sheet = gc.open(SHEET_NAME).worksheet("Raw Data: Inventory")

# API Credentials
API_KEY = os.getenv("API_KEY")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
API_ACCESS_TOKEN = os.getenv("API_ACCESS_TOKEN")
SHOP_NAME = os.getenv("SHOP_NAME")

# Define the API endpoint
url = f"https://{SHOP_NAME}.myshopify.com/admin/api/2023-04/products.json"

# Set the headers including the access token
headers = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": API_ACCESS_TOKEN
}

# Database file path
db_file = "shopify.db"

# Function to create a database and table if it doesn't exist
def setup_database():
    conn = sqlite3.connect(db_file)

    # Query the data from the products table
    df = pd.read_sql_query("SELECT * FROM products", conn)
    
    # Convert the df to a list of lists 
    data = [df.columns.tolist()] + df.values.tolist()

    cursor = conn.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS products (
            SKU TEXT,
            PRODUCT_ID INTEGER, 
            PRODUCT TEXT,
            SIZE TEXT,
            PRICE REAL,
            INVENTORY_QUANTITY INTEGER
        )
        '''
    )
    conn.commit()
    conn.close()

    # Clear the sheet
    sheet.clear()

    # Update the sheet with new data
    sheet.update(range_name="A1", values=data)

# Function to fetch data from Shopify API and insert into SQLite
def fetch_and_save_data_to_sqlite():
    # Make the GET request to the Shopify API
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Parse the JSON response
        products = response.json()

        # Create a list of dictionaries for the products
        products_list = [
            {
                "SKU": variant.get("sku"),
                "Product ID": product.get("id"),
                "Product": product.get("title"),
                "Size": variant.get("title"),
                "Price": float(variant.get("price", 0)),
                "Inventory Quantity": int(variant.get("inventory_quantity", 0))
            }
            for product in products.get("products", [])
            for variant in product.get("variants", [])
        ]

        # Convert to a Pandas DataFrame
        df = pd.DataFrame(products_list)

        # Insert the data into SQLite
        conn = sqlite3.connect(db_file)
        try:
            df.to_sql("products", conn, if_exists="replace", index=False)
            print(f"Data successfully inserted into {db_file} at {datetime.now()}")
        except Exception as e:
            print(f"Error inserting data: {e}")
        finally:
            conn.close()
    else:
        print(f"Failed to fetch data. Error {response.status_code}: {response.text}")

# Setup the database (create table if not exists)
setup_database()

# Fetch and save data into the database
fetch_and_save_data_to_sqlite()

print("Database file path:", os.path.abspath(db_file))


