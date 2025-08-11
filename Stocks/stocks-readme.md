# Real-Time Stock Price WebSocket Consumer

This project includes a Django Channels **WebSocket consumer** that fetches **real-time stock prices** from Finnhub and streams them directly to the smart mirror.

---

## How It Works:

1. The smart-mirror front-end connects to ws/stocks/
2. The websocket consumer (stocksConsumer) starts running
3. checks for logged in user: if logged in it fetches user saved stock preferences, if not it uses defualt stocks [AAPL, TSLA]
4. The consumer opens a websocket connection to finnhub
5. It subscribes to the requested stocks
6. live prices stream back from finnhub
7. THe consumer forwards the info back to the smart mirror front end

---

##  Key Features

-  **Fully async design using Django Channels.**
-  **Auto-reconnect if Finnhub disconnects.**
-  **Real-time updates directly from Finnhub.**
-  **Personalized to each user's saved stocks (if logged in).**
-  **Supports anonymous users with default stocks.**



## Code Structure

| File | Purpose |
|---|---|
| `consumers.py` | Core WebSocket consumer logic (subscribe, fetch, forward). |
| `routing.py` | Maps `/ws/Stocks/` URL to `StocksConsumer`. |
| `models.py` | Contains `StockPreference` model for saving user stock choices. |
| `asgi.py` | Configures Django Channels and WebSockets for the project. |



## How to Run
1. Set the Django environment variable(needed for Daphne to recognize settings):

    $env:DJANGO_SETTINGS_MODULE="smart_mirror_project.settings"

2. Start Daphne:
    
    daphne smart_mirror_project.asgi:application
    
3. Connect from the smart mirror frontend using:
    
    ws://localhost:8000/ws/Stocks/
    
4. Live stock data will stream



## Key Functions Explained

### `connect()`

- Accepts the WebSocket connection.
- Loads user stock preferences (or defaults).
- Starts background task to fetch live prices.

### `get_user_stock_preferences()`

- Fetches the user’s saved stocks from the database.
- Defaults to AAPL & TSLA for anonymous users.

### `stream_stock_data()`

- Opens a WebSocket connection to **Finnhub**.
- Subscribes to each stock symbol.
- Streams live data back to the mirror frontend.

---

## Data Flow Diagram

```text
Smart Mirror UI
    |
    |  (Connects via WebSocket)
    |
    V
Django Channels (StocksConsumer)
    |
    |  (Connects to Finnhub via WebSocket)
    |
    V
Finnhub (Real-time Stock Data)
    |
    |  (Live prices stream back)
    |
    V
Django Channels (forwards to Smart Mirror UI)
