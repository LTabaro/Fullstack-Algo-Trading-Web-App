"""
Run this script once a day towards the close to clean up our portfolio and existing trades
and anything else we want to do towards the end of the day,
maybe we want to send notifications towards the end of the day etc
"""

from alpaca_trade_api.rest import REST
import config


def initialize_api():
    return REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)


def close_portfolio_positions(api_client):
    api_client.close_all_positions() # close all open positions in the portfolio


if __name__ == "__main__":
    # Main execution block
    alpaca_client = initialize_api()
    close_portfolio_positions(alpaca_client)
