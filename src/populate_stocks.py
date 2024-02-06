"""
populating stock table in database with tradable stocks using Alpaca api
"""
import sqlite3, config
import alpaca_trade_api as tradeapi


conn = sqlite3.connect(config.DB_FILE)
conn.row_factory = sqlite3.Row

c = conn.cursor()

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
assets = api.list_assets()


c.execute("SELECT symbol, name FROM stock")
rows = c.fetchall()
symbols = [row['symbol'] for row in rows]


for asset in assets:
    try:
        if asset.status == 'active' and asset.tradable and asset.symbol not in symbols:
            print(f"Added a new stock {asset.symbol}{asset.name}")
            c.execute("INSERT INTO stock (symbol, name, exchange, shortable) VALUES (?,?, ?, ?)", (asset.symbol, asset.name, asset.exchange, asset.shortable))
    except Exception as e:
        print(asset.symbol)
        print(e)
conn.commit()


conn.close()
