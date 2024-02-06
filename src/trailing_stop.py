import config
import alpaca_trade_api as tradeapi
from helpers import calculate_quantity

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

symbols = ['SPY', 'IwM', 'DIA']

for symbol in symbols:
    quote = api.get_latest_quote(symbol)

    api.submit_order(
        symbol=symbol,
        side='buy',
        type='market',
        qty=calculate_quantity(quote.bidprice),
        time_in_force='day'
    )

orders = api.list_orders()
positions = api.list_positions()

api.submit_order(
    symbol='IwM', # the symbols which have been confirmed by the orders and positions variables
    side='sell',
    qty=57, # you can choose to sell less than the quantity you bought and take partial profit then let the rest run
    time_in_force='day',
    type='trailing_stop',
    trail_price='0.20'

)

api.submit_order(
    symbol='DIA',  # the symbols which have been confirmed by the orders and positions variables
    side='sell',
    qty=5,
    time_in_force='day',
    type='trailing_stop',
    trail_percent='0.70'

)