from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
import sqlite3, config
from fastapi.templating import Jinja2Templates
from datetime import date
import alpaca_trade_api as tradeapi


app = FastAPI()
templates = Jinja2Templates(directory="templates")
current_date = date.today().isoformat()


@app.get("/")
def index(request: Request):
    stock_filter = request.query_params.get('filter', False)
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if stock_filter == 'new_closing_highs':
        c.execute(
            """SELECT * FROM (SELECT symbol, name, stock_id, max(close), date 
            FROM stock_price JOIN stock ON stock.id = stock_price.stock_id 
            GROUP BY stock_id ORDER BY symbol
            ) WHERE date = (SELECT max(date) FROM stock_price)
            """)

    elif stock_filter == 'new_closing_lows':
        c.execute(
            """SELECT * FROM (SELECT symbol, name, stock_id, min(close), date 
            FROM stock_price JOIN stock ON stock.id = stock_price.stock_id 
            GROUP BY stock_id ORDER BY symbol
            ) WHERE date = (SELECT max(date) FROM stock_price)
            """)

    elif stock_filter == 'rsi_overbought':
        c.execute(
            """SELECT symbol, name, stock_id, date 
            FROM stock_price JOIN stock ON stock.id = stock_price.stock_id
            WHERE rsi_14 > 70
            AND date = (SELECT max(date) FROM stock_price)
            ORDER BY symbol
            """)
    elif stock_filter == 'rsi_oversold':
        c.execute(
            """SELECT symbol, name, stock_id, date 
            FROM stock_price JOIN stock ON stock.id = stock_price.stock_id
            WHERE rsi_14 < 30
            AND date = (SELECT max(date) FROM stock_price)
            ORDER BY symbol
            """)

    elif stock_filter == 'above_sma_20':
        c.execute(
            """SELECT symbol, name, stock_id, date 
            FROM stock_price JOIN stock ON stock.id = stock_price.stock_id
            WHERE close > sma_20
            AND date = (SELECT max(date) FROM stock_price)
            ORDER BY symbol
            """)
    elif stock_filter == 'below_sma_20':
        c.execute(
            """SELECT symbol, name, stock_id, date 
            FROM stock_price JOIN stock ON stock.id = stock_price.stock_id
            WHERE close < sma_20
            AND date = (SELECT max(date) FROM stock_price)
            ORDER BY symbol
            """)
    elif stock_filter == 'above_sma_50':
        c.execute(
            """SELECT symbol, name, stock_id, date 
            FROM stock_price JOIN stock ON stock.id = stock_price.stock_id
            WHERE close > sma_50
            AND date = (SELECT max(date) FROM stock_price)
            ORDER BY symbol
            """)
    elif stock_filter == 'below_sma_50':
        c.execute(
            """SELECT symbol, name, stock_id, date 
            FROM stock_price JOIN stock ON stock.id = stock_price.stock_id
            WHERE close < sma_50
            AND date = (SELECT max(date) FROM stock_price)
            ORDER BY symbol
            """)
    else:
        c.execute("SELECT id, symbol, name FROM stock ORDER BY symbol")
    rows = c.fetchall()

    c.execute(
        """SELECT symbol, rsi_14, sma_20, sma_50, close
        FROM stock JOIN stock_price ON stock_price.stock_id = stock.id
        WHERE date = ?;
    """, (current_date,))
    indicator_rows = c.fetchall()
    indicator_values = {}
    for row in indicator_rows:
        indicator_values[row['symbol']] = row

    print(indicator_values)
    return templates.TemplateResponse("index.html", {"request": request, "stocks":rows, "indicator_values": indicator_values})


@app.get("/stock/{symbol}")
def stock_detail(request: Request, symbol):
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
    SELECT * FROM strategy
    """)

    strategies = c.fetchall()
    c.execute("SELECT id, symbol, name FROM stock WHERE symbol = ?", (symbol,))
    row = c.fetchone()

    c.execute("SELECT * FROM stock_price WHERE stock_id = ? ORDER BY date DESC", (row['id'],))
    prices = c.fetchall()
    return templates.TemplateResponse("stock_detail.html", {"request": request, "stock": row, "bars": prices, "strategies":strategies})


@app.post("/apply_strategy")
def apply_strategy(strategy_id: int = Form(...), stock_id: int = Form(...)):
    conn = sqlite3.connect(config.DB_FILE)
    c = conn.cursor()

    c.execute("""
        INSERT INTO stock_strategy (stock_id, strategy_id) VALUES (?, ?) 
        """, (stock_id, strategy_id))

    conn.commit()
    return RedirectResponse(url=f"/strategy/{strategy_id}", status_code=303)


@app.get("/strategies")
def strategies(request: Request):
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
    SELECT * FROM strategy
    """)

    strategies = c.fetchall()

    return templates.TemplateResponse("strategies.html", {"request": request, "strategies": strategies})


@app.get("/orders")
def orders(request: Request):
    api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
    orders = api.list_orders(status='all')
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders})


@app.get("/strategy/{strategy_id}")
def strategy(request: Request, strategy_id):
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
    SELECT id, name
    FROM strategy
    WHERE id = ?
    """, (strategy_id,))

    strategy = c.fetchone()

    c.execute("""
    SELECT symbol, name
    FROM stock JOIN stock_strategy on stock_strategy.stock_id = stock.id
    WHERE strategy_id = ?
    """, (strategy_id,))
    stocks = c.fetchall()
    return templates.TemplateResponse("strategy.html", {"request": request, "stocks": stocks, "strategy": strategy})


