from alpaca_trade_api.rest import REST
import config
from utils import calculate_quantity


def initialize_api_client():
    # set up the Alpaca API client
    return REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)


def place_market_orders(api_client, symbols):
    # execute market orders for a list of symbols
    for ticker in symbols:
        latest_quote = api_client.get_latest_quote(ticker)
        quantity = calculate_quantity(latest_quote.bidprice)
        api_client.submit_order(
            symbol=ticker,
            side='buy',
            type='market',
            qty=quantity,
            time_in_force='day'
        )


def apply_trailing_stop(api_client, symbol, quantity, stop_type, stop_value):
    # apply a trailing stop order to manage risk
    api_client.submit_order(
        symbol=symbol,
        side='sell',
        qty=quantity,
        time_in_force='day',
        type='trailing_stop',
        **{stop_type: stop_value}
    )


def confirm_orders_and_positions(api_client, symbol, quantity, stop_type, stop_value):
    # check current orders and positions, then apply a trailing stop
    current_orders = api_client.list_orders()
    current_positions = api_client.list_positions()

    # Assuming the presence of the symbol in orders and positions is confirmed
    apply_trailing_stop(api_client, symbol, quantity, stop_type, stop_value)


if __name__ == "__main__":
    alpaca_client = initialize_api_client()  # Initialize API connection

    target_symbols = ['SPY', 'IwM', 'DIA']
    place_market_orders(alpaca_client, target_symbols)  # Place market buy orders

    # applying trailing stops for selected symbols based on confirmed orders/positions
    confirm_orders_and_positions(alpaca_client, 'QQQ', 42, 'trail_price', '0.20')
    confirm_orders_and_positions(alpaca_client, 'XLK', 9, 'trail_percent', '0.70')
