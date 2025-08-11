import json
import asyncio 
import websockets
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async #the glue that holds synchronous and asynchonorous calls together
from django.apps import apps
from django.conf import settings


class StocksConsumer(AsyncWebsocketConsumer):

    #first function, does all the heavy lifting
    async def connect(self): 
        await self.accept() #establishes connection with the websocket channel, uses await to not block the server while waiting for connections
        self.user = self.scope.get('user') #gets the user or ananymous
        self.symbols = await self.get_user_stock_preferences() #calls an instance of the get_user_stock_preferences() function to get stock preferences

        print(f" Subscribing to symbols for {self.user if self.user.is_authenticated else 'Anonymous'}: {self.symbols}") #simple log check to make sure it's subscribing once connected

        self.task = asyncio.create_task(self.stream_stock_data()) #creates a variable called task that allows the streaming of the users stock data

    #disconnects server
    async def disconnect(self, close_code):
        if hasattr(self, 'task'):
            self.task.cancel()

    #grabs user stock preferences form database if applicable, otherwise uses default tickers
    async def get_user_stock_preferences(self):
        if not self.user.is_authenticated:
            return ["AAPL", "TSLA"]

        StockPreference = apps.get_model('Stocks', 'StockPreference')
        try:
            stock_pref = await sync_to_async(StockPreference.objects.get)(user=self.user) #uses sync_to_async because django channels needs everything to be async because sync are blocking
            return [
                stock_pref.stock_preference_one,
                stock_pref.stock_preference_two,
                stock_pref.stock_preference_three,
                stock_pref.stock_preference_four,
            ]
        except StockPreference.DoesNotExist:
            return ["AAPL", "TSLA"]

    #function that connects to finhub and outputs user subscriptions or defaults
    async def stream_stock_data(self):
        print(" stream_stock_data() started")
        socket_url = f"wss://ws.finnhub.io?token={settings.STOCKS_API_KEY}"
        
        #try block to catch errors
        try:
            async with websockets.connect(socket_url) as ws: #creates live websocket object (ws)
                for symbol in self.symbols:
                    await ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))

                while True:
                    msg = await ws.recv() #collects the data recieved from finnhub
                    await self.send(msg) #sends it to the front end

        except Exception as e:
            print(f" WebSocket error in stream_stock_data: {e}")
