"""
Bollinger band trading strategy implementation
"""

import sqlite3
import config
import alpaca_trade_api as tradeapi
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import tulipy as ti
from datetime import date


current_date = date.today().isoformat()
print(current_date)

conn = sqlite3.connect(config.DB_FILE)
conn.row_factory = sqlite3.Row

c = conn.cursor()

c.execute("""
SELECT id FROM strategy WHERE name = 'bollinger_bands'
""")

strategy_id = c.fetchone()['id']

c.execute("""
SELECT symbol, name 
FROM stock
JOIN stock_strategy ON stock_strategy.stock_id = stock.id
WHERE stock_strategy.strategy_id = ?
""", (strategy_id,))

stocks = c.fetchall()
symbols = [stock['symbol'] for stock in stocks]
print(symbols)

current_date = date.today().isoformat()

start_minute_bar = f"{current_date} 09:30:00-05:00"
end_minute_bar = f"{current_date} 16:00:00-05:00"  # start and end is now the full day 9:30 - 4

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
orders = api.list_orders(status='all', after=current_date) # after market opens today UTC time
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']


def get_minute_data(ticker, date):
    ts = TimeSeries(key=config.ALPHA_KEY, output_format='pandas', indexing_type='date')
    df, _ = ts.get_intraday(ticker, interval='1min', outputsize='full')

    df.rename(columns={"1. open": "open", "2. high": "high", "3. low": "low", "4. close": "close",
                       "5. volume": "volume"}, inplace=True)

    # Filter for rows on the specified date
    df = df[df.index.date == pd.to_datetime(date).date()]

    return df


messages = []
for symbol in symbols:
    minute_bars = get_minute_data(symbol, current_date) # MAX 25 API REQUESTS PER DAY

    market_open_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
    market_open_bars = minute_bars.loc[market_open_mask]

    if len(market_open_bars) >= 20:
        closes = market_open_bars.close.values
        lower, middle, upper = ti.bbands(closes, 20, 2) # 2 standard deviations
        current_candle = market_open_bars.iloc[-1]
        previous_candle = market_open_bars.iloc[-2]

        if current_candle.close > lower[-1] and previous_candle.close < lower[-2]:
            print(f"{symbol} closed above lower bollinger band")
            print(current_candle)
            if symbol not in existing_order_symbols:
                limit_price = current_candle.close
                candle_range = current_candle.high - current_candle.low 

                message = f"placing order for {symbol} at {limit_price} \n\n"
                messages.append(message)
                print(message)

                try:

                    api.submit_order(
                        symbol=symbol,
                        side='buy',
                        type='limit',
                        qty=100,
                        time_in_force='day',
                        order_class='bracket',
                        limit_price=limit_price,
                        take_profit=dict(
                            limit_price=limit_price + candle_range * 3,
                        ),
                        stop_loss=dict(
                            stop_price=previous_candle.low,
                        )

                    )
                except Exception as e:
                    print(f"could not submit order {e}")
            else:
                print(f"Already and order for {symbol}, skipping")
