"""
populating stock table in database with tradeable stocks using Alpaca api
"""

import sqlite3
from alpaca_trade_api import REST
import config


def initialize_db_connection():
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def fetch_existing_symbols(cursor):
    cursor.execute("SELECT symbol, name FROM stock")
    existing_rows = cursor.fetchall()
    return [row['symbol'] for row in existing_rows]


def add_new_stocks(cursor, tradable_assets, existing_symbols):
    # add new stocks to the database that are active, tradable, and not already in the database
    for asset in tradable_assets:
        try:
            if asset.status == 'active' and asset.tradable and asset.symbol not in existing_symbols:
                print(f"Adding new stock: {asset.symbol} ({asset.name})")
                cursor.execute(
                    "INSERT INTO stock (symbol, name, exchange, shortable) VALUES (?, ?, ?, ?)",
                    (asset.symbol, asset.name, asset.exchange, asset.shortable)
                )
        except Exception as error:
            print(f"Error adding {asset.symbol}: {error}")


def main():
    alpaca_client = REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
    connection = initialize_db_connection()
    cursor = connection.cursor()

    tradable_assets = alpaca_client.list_assets()
    existing_symbols = fetch_existing_symbols(cursor)

    add_new_stocks(cursor, tradable_assets, existing_symbols)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    main()
