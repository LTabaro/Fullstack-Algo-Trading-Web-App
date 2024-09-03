from datetime import date
import sqlite3
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import alpaca_trade_api as tradeapi
import config

# Initialize the FastAPI application and templates
app = FastAPI()
template_engine = Jinja2Templates(directory="templates")

# Get today's date as a string
today_str = date.today().isoformat()


# Function to establish a database connection
def establish_db_connection():
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


# Helper function to fetch stock data based on filters
def fetch_stock_data(cursor, filter_criteria):
    filter_queries = {
        'new_closing_highs': """
            SELECT * FROM (
                SELECT symbol, name, stock_id, MAX(close) AS max_close, date 
                FROM stock_price 
                JOIN stock ON stock.id = stock_price.stock_id 
                GROUP BY stock_id 
                ORDER BY symbol
            ) WHERE date = (SELECT MAX(date) FROM stock_price)
        """,
        'new_closing_lows': """
            SELECT * FROM (
                SELECT symbol, name, stock_id, MIN(close) AS min_close, date 
                FROM stock_price 
                JOIN stock ON stock.id = stock_price.stock_id 
                GROUP BY stock_id 
                ORDER BY symbol
            ) WHERE date = (SELECT MAX(date) FROM stock_price)
        """,
        'rsi_overbought': """
            SELECT symbol, name, stock_id, date 
            FROM stock_price 
            JOIN stock ON stock.id = stock_price.stock_id
            WHERE rsi_14 > 70 AND date = (SELECT MAX(date) FROM stock_price)
            ORDER BY symbol
        """,
        'rsi_oversold': """
            SELECT symbol, name, stock_id, date 
            FROM stock_price 
            JOIN stock ON stock.id = stock_price.stock_id
            WHERE rsi_14 < 30 AND date = (SELECT MAX(date) FROM stock_price)
            ORDER BY symbol
        """,
        'above_sma_20': """
            SELECT symbol, name, stock_id, date 
            FROM stock_price 
            JOIN stock ON stock.id = stock_price.stock_id
            WHERE close > sma_20 AND date = (SELECT MAX(date) FROM stock_price)
            ORDER BY symbol
        """,
        'below_sma_20': """
            SELECT symbol, name, stock_id, date 
            FROM stock_price 
            JOIN stock ON stock.id = stock_price.stock_id
            WHERE close < sma_20 AND date = (SELECT MAX(date) FROM stock_price)
            ORDER BY symbol
        """,
        'above_sma_50': """
            SELECT symbol, name, stock_id, date 
            FROM stock_price 
            JOIN stock ON stock.id = stock_price.stock_id
            WHERE close > sma_50 AND date = (SELECT MAX(date) FROM stock_price)
            ORDER BY symbol
        """,
        'below_sma_50': """
            SELECT symbol, name, stock_id, date 
            FROM stock_price 
            JOIN stock ON stock.id = stock_price.stock_id
            WHERE close < sma_50 AND date = (SELECT MAX(date) FROM stock_price)
            ORDER BY symbol
        """
    }

    if filter_criteria in filter_queries:
        cursor.execute(filter_queries[filter_criteria])
    else:
        cursor.execute("SELECT id, symbol, name FROM stock ORDER BY symbol")

    return cursor.fetchall()


# Endpoint to render the homepage with filtered stock data
@app.get("/")
async def render_homepage(request: Request):
    db_conn = establish_db_connection()
    cursor = db_conn.cursor()

    filter_type = request.query_params.get('filter', None)
    stock_records = fetch_stock_data(cursor, filter_type)

    cursor.execute("""
        SELECT symbol, rsi_14, sma_20, sma_50, close 
        FROM stock 
        JOIN stock_price ON stock_price.stock_id = stock.id 
        WHERE date = ?
    """, (today_str,))
    indicator_data = cursor.fetchall()

    indicators = {record['symbol']: record for record in indicator_data}

    return template_engine.TemplateResponse("home.html", {
        "request": request,
        "stocks": stock_records,
        "indicator_values": indicators
    })


# Endpoint to show details for a specific stock
@app.get("/stock/{symbol}")
async def show_stock_details(request: Request, symbol: str):
    db_conn = establish_db_connection()
    cursor = db_conn.cursor()

    cursor.execute("SELECT id, symbol, name FROM stock WHERE symbol = ?", (symbol,))
    stock_info = cursor.fetchone()

    cursor.execute("SELECT * FROM stock_price WHERE stock_id = ? ORDER BY date DESC", (stock_info['id'],))
    stock_prices = cursor.fetchall()

    cursor.execute("SELECT * FROM strategy")
    available_strategies = cursor.fetchall()

    return template_engine.TemplateResponse("stock_detail.html", {
        "request": request,
        "stock": stock_info,
        "bars": stock_prices,
        "strategies": available_strategies
    })


# Endpoint to apply a strategy to a stock
@app.post("/apply_strategy")
async def apply_selected_strategy(strategy_id: int = Form(...), stock_id: int = Form(...)):
    db_conn = establish_db_connection()
    cursor = db_conn.cursor()

    cursor.execute("""
        INSERT INTO stock_strategy (stock_id, strategy_id) 
        VALUES (?, ?)
    """, (stock_id, strategy_id))

    db_conn.commit()

    return RedirectResponse(url=f"/strategy/{strategy_id}", status_code=303)


# Endpoint to list all strategies
@app.get("/strategies")
async def list_all_strategies(request: Request):
    db_conn = establish_db_connection()
    cursor = db_conn.cursor()

    cursor.execute("SELECT * FROM strategy")
    strategies = cursor.fetchall()

    return template_engine.TemplateResponse("strategies.html", {
        "request": request,
        "strategies": strategies
    })


# Endpoint to display order history
@app.get("/orders")
async def list_all_orders(request: Request):
    alpaca_client = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
    order_history = alpaca_client.list_orders(status='all')

    return template_engine.TemplateResponse("trade_history.html", {
        "request": request,
        "orders": order_history
    })


# Endpoint to display strategy details
@app.get("/strategy/{strategy_id}")
async def show_strategy_details(request: Request, strategy_id: int):
    db_conn = establish_db_connection()
    cursor = db_conn.cursor()

    cursor.execute("SELECT id, name FROM strategy WHERE id = ?", (strategy_id,))
    strategy_info = cursor.fetchone()

    cursor.execute("""
        SELECT symbol, name 
        FROM stock 
        JOIN stock_strategy ON stock_strategy.stock_id = stock.id 
        WHERE strategy_id = ?
    """, (strategy_id,))
    related_stocks = cursor.fetchall()

    return template_engine.TemplateResponse("strategy.html", {
        "request": request,
        "stocks": related_stocks,
        "strategy": strategy_info
    })



