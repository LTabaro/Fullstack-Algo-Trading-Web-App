"""
Populating the stock_price table for all stock symbols in the stock table
"""
import sqlite3, config
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame
import tulipy as ti
import numpy as np
from datetime import date

current_date = date.today().isoformat()

START = "2023-08-24"
END = current_date

conn = sqlite3.connect(config.DB_FILE)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT id, symbol, name FROM stock")
stocks = c.fetchall()

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

"""
Alpaca market data api lets you request price data of up to 200 symbols at a time.
We have 10000+ stocks so to avoid making 1000s of api requests we'll loop through them 200 at a time instead of 1 by 1.
"""

chunk_size = 200

# Process stocks in chunks
for i in range(0, len(stocks), chunk_size):
    symbol_chunk = [stock['symbol'] for stock in stocks[i:i + chunk_size]]

    try:
        # Fetch bars for all symbols in the chunk
        bars = api.get_bars(symbol_chunk, TimeFrame.Day, start=START, end=END).df

        for stock in stocks[i:i + chunk_size]:
            # Filter bars for the current stock
            symbol_bars = bars[bars['symbol'] == stock['symbol']]

            if not symbol_bars.empty:
                # Calculate indicators if there are enough data points
                if len(symbol_bars) >= 50:
                    sma_20 = ti.sma(np.array(symbol_bars['close']), period=20)[-1]
                    sma_50 = ti.sma(np.array(symbol_bars['close']), period=50)[-1]
                    rsi_14 = ti.rsi(np.array(symbol_bars['close']), period=14)[-1]
                else:
                    sma_20, sma_50, rsi_14 = None, None, None

                # Insert data into the database
                for index, row in symbol_bars.iterrows():
                    c.execute("""
                        INSERT INTO stock_price (stock_id, date, open, high, low, close, volume, sma_20, sma_50, rsi_14)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (stock['id'], index.date(), row['open'], row['high'], row['low'], row['close'], row['volume'],
                         sma_20 if index == symbol_bars.index[-1] else None,
                         sma_50 if index == symbol_bars.index[-1] else None,
                         rsi_14 if index == symbol_bars.index[-1] else None))
    except tradeapi.rest.APIError as e:
        print(f"An error occurred with chunk starting at symbol {symbol_chunk[0]}: {e}")

    conn.commit()

conn.close()














