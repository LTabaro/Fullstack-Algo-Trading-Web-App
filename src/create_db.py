import sqlite3
import config


conn = sqlite3.connect(config.DB_FILE)
c = conn.cursor()

table_1 = """ CREATE TABLE IF NOT EXISTS stock (
id INTEGER PRIMARY KEY,
symbol TEXT NOT NULL UNIQUE,
name TEXT NOT NULL,
exchange TEXT NOT NULL,
shortable BOOLEAN NOT NULL
)"""
table_2 = """ CREATE TABLE IF NOT EXISTS stock_price (
id INTEGER PRIMARY KEY,
stock_id INTEGER,
date NOT NULL,
open NOT NULL,
high NOT NULL,
low NOT NULL,
close NOT NULL,
volume NOT NULL,
sma_20,
sma_50,
rsi_14,
FOREIGN KEY (stock_id) REFERENCES stock (id)

)"""

table_3 = """ CREATE TABLE IF NOT EXISTS strategy (
id INTEGER PRIMARY KEY,
name NOT NULL
)"""

table_4 = """ CREATE TABLE IF NOT EXISTS stock_strategy (
stock_id INTEGER NOT NULL,
strategy_id INTEGER NOT NULL,
FOREIGN KEY (stock_id) REFERENCES stock (id)
FOREIGN KEY (strategy_id) REFERENCES strategy (id)
)"""

table_5 = """CREATE TABLE IF NOT EXISTS stock_price_minute (
id INTEGER PRIMARY KEY, 
stock_id INTEGER,
datetime NOT NULL,
open NOT NULL,
high NOT NULL,
low NOT NULL,
close NOT NULL, 
volume NOT NULL,
FOREIGN KEY (stock_id) REFERENCES stock (id)
)"""


c.execute(table_1)
c.execute(table_2)
c.execute(table_3)
c.execute(table_4)
c.execute(table_5)

strategies = ['opening_range_breakout', 'opening_range_breakdown', 'bollinger_bands']

for strategy in strategies:
    c.execute("""
    INSERT INTO strategy (name) VALUES (?)
    """, (strategy,))


conn.commit()
conn.close()
