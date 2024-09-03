import sqlite3
import config
import alpaca_trade_api as tradeapi
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import smtplib, ssl
from datetime import date
from regional_time import is_dst


current_date = date.today().isoformat()
print(current_date)

# Create a secure SSL context
context = ssl.create_default_context()

conn = sqlite3.connect(config.DB_FILE)
conn.row_factory = sqlite3.Row

c = conn.cursor()

c.execute("""
SELECT id FROM strategy WHERE name = 'opening_range_breakdown'
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

if is_dst():
    start_minute_bar = f"{current_date} 09:30:00-05:00"
    end_minute_bar = f"{current_date} 09:45:00-05:00"
else:
    start_minute_bar = f"{current_date} 09:30:00-04:00"
    end_minute_bar = f"{current_date} 09:45:00-04:00"


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
    print(symbol)
    # print(minute_bars)
    opening_range_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
    opening_range_bars = minute_bars.loc[opening_range_mask]
    opening_range_low = opening_range_bars['low'].min()
    opening_range_high = opening_range_bars['high'].max()
    opening_range = opening_range_high - opening_range_low

    after_opening_range_mask = minute_bars.index >= end_minute_bar
    after_opening_range_bars = minute_bars.loc[after_opening_range_mask]
    after_opening_range_breakdown = after_opening_range_bars[after_opening_range_bars['close'] < opening_range_low]

    if not after_opening_range_breakdown.empty:
        if symbol not in existing_order_symbols:
            limit_price = after_opening_range_breakdown.iloc[0]['close']

            message = f"selling short {symbol} at {limit_price}, closed below {opening_range_low}\n\n{after_opening_range_breakdown.iloc[0]}\n\n"
            messages.append(message)
            print(message)

            try:
                api.submit_order(
                    symbol=symbol,
                    side='sell',
                    type='limit',
                    qty=100,
                    time_in_force='day',
                    order_class='bracket',
                    limit_price=limit_price,
                    take_profit=dict(
                        limit_price=limit_price - opening_range,
                    ),
                    stop_loss=dict(
                        stop_price=limit_price + opening_range,
                    )

                )
            except Exception as e:
                print(f"could not submit order {e}")
        else:
            print(f"Already and order for {symbol}, skipping")

print(messages)
with smtplib.SMTP_SSL(config.EMAIL_HOST, config.EMAIL_PORT, context=context) as server:
    server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
    email_message = f"Subject: Trade Notifications for {current_date}\n\n"
    email_message += "\n\n".join(messages)
    server.sendmail(config.EMAIL_ADDRESS, config.EMAIL_ADDRESS, email_message)
