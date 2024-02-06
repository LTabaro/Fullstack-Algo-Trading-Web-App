"""
Run this script once a day towards the close to clean up our portfolio and existing trades
and anything else we want to do towards the end of the day,
maybe we want to send notifications towards the end of the day etc
"""
import config
import alpaca_trade_api as tradeapi
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
api.close_all_positions()
