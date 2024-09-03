# Algorithmic Trading Web Application
This project is a comprehensive algorithmic trading web application developed in Python using the Alpaca API. The application enables users to manage their order and portfolio positions, apply trading strategies, and receive real-time notifications.

## Features
* Trading Strategies: Implements Bollinger Band and Opening Range Breakout (ORB) strategies for automated trading decisions.
* RESTful API: Built with the FastAPI framework and powered by the uvicorn web server, providing a robust backend for the application.
* Job Scheduling: Utilizes Crontab job scheduling to regularly update records in the SQL database with new symbols and price data.
* Frontend Interface: A feature-rich frontend allows users to filter stocks based on recent performance, create personalized watchlists, select trading strategies, and receive instant trade notifications via email and SMS.
* Portfolio Management: Users can view and manage their portfolio positions, with real-time updates and detailed analytics.

## Usage
### Managing Orders and Portfolio Positions
* Placing Orders: Users can place market, limit, and stop orders for stocks and ETFs directly from the application.
* Viewing Positions: The portfolio management section provides a real-time view of all open positions, including profit/loss details.
### Applying Trading Strategies
* Bollinger Band Strategy: Automatically trades based on the Bollinger Band strategy, which identifies overbought and oversold conditions.
* Opening Range Breakout (ORB) Strategy: Implements the ORB strategy, which looks for significant price movements within the first hour of trading.
### Notifications
* Email and SMS Alerts: Users receive instant notifications when a buy or sell order is executed, ensuring they are always informed about their trading activities.


## References

- **Alpaca API**:
  - [Alpaca Github](https://github.com/alpacahq/alpaca-trade-api-python)

- **Backtesting**:
  - [Backtrader Quickstart](https://backtrader.com/docu/quickstart/quickstart/)

- **Webpage Design**:
  - [Semantic UI Getting Started](https://semantic-ui.com/introduction/getting-started.html)

- **Tutorial**:
  - [Part Time Larry's Youtube Tutorial](https://www.youtube.com/playlist?list=PLvzuUVysUFOuoRna8KhschkVVUo2E2g6G)

