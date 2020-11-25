import asyncio
import datetime
import json
import logging
import pathlib
import ssl
import sys
import traceback
import websockets
from os import path

MAX_SYMBOLS = 50 # Hard limit imposed by FinnHub

class FinnhubClient:
  """
  Maintains a websocket connection with the FinnHub data source.
  Keeps track of subscriptions to avoid sending duplicate subscription requests 
  in the case where more than one client subscribes to the same symbol.
  Has a reference to the server for passing price updates.
  """
  URI = "wss://ws.finnhub.io?token=bqq9i0nrh5r9ffdhino0"

  def __init__(self, setServerInstance=None):
    self.serverInstance = setServerInstance
    self.websocket = None
    self.subscriptions = set()
    self.logger = logging.getLogger('dlove.it.Tikka.FinnhubClient')

  def setServerInstance(self, serverInstance):
    self.serverInstance = serverInstance

  async def run(self):
    while True:
      try:
        self.logger.info("Connecting to FinnHub...")
        async with websockets.connect(FinnhubClient.URI) as websocket:
          self.logger.info("Connected.")
          self.websocket = websocket
          self.subscriptions = set()
          async for message in websocket:
            self.logger.debug(f"< {message}")
            message = json.loads(message)
            if (message.get('type', None) == 'trade'):
              symbol = message['data'][-1]['s']
              price = message['data'][-1]['p']
              await self.updateOnServer(symbol, price)
      except (ConnectionRefusedError, websockets.exceptions.WebSocketException) as e:
        self.logger.error(f"FinnhubClient: {type(e)}")
        self.logger.exception(e)
        await asyncio.sleep(5)
        continue

  async def updateOnServer(self, symbol, price):
    await self.serverInstance.updatePrice(symbol, price)

  async def subscribe(self, symbol):
    self.logger.debug(f"FinnhubClient.subscribe({symbol})")
    if symbol not in self.subscriptions:
      self.subscriptions.add(symbol)
      event = self.subscribeEvent(symbol)
      await self.websocket.send(event)

  async def unsubscribe(self, symbol):
    self.logger.debug(f"FinnhubClient.unsubscribe({symbol})")
    if symbol in self.subscriptions:
      self.subscriptions.remove(symbol)
      event = self.unsubscribeEvent(symbol)
      await self.websocket.send(event)

  def subscribeEvent(self, symbol):
    return json.dumps({"type":"subscribe", "symbol": symbol})

  def unsubscribeEvent(self, symbol):
    return json.dumps({"type":"unsubscribe", "symbol": symbol})


class TikkaServer:
  """
  Handles connections and subscribe/unsubscribe requests from web clients.
  Sends price updates to subscribers over their respective websockets.
  Maintains a dict of subscribers:   a map of websocket -> symbol.
        And a dict of subscriptions: a map of symbol -> websocket.
  Clients are removed from both lists when they disconnect.
  Has a reference to FinnhubClient for passing subscribe/unsubscribe requests.
  """
  def __init__(self, clientInstance=None):
    self.clientInstance = clientInstance
    self.subscriptions = {}
    self.subscribers = {}
    self.logger = logging.getLogger('dlove.it.Tikka.TikkaServer')

  def setClientInstance(self, clientInstance):
    self.clientInstance = clientInstance

  async def run(self, websocket, path):
    self.logger.debug("Connection established.")
    await self.addSubscriber(websocket)

    try:
      async for message in websocket:
        self.logger.debug(f"< {message}")

        # get symbol and command (subscribe/unsubscribe) from message
        message = json.loads(message)
        command = message.get('type', None)
        symbol = message.get('symbol', None)

        # call subscribe/unsubscribe on finnhub client
        if (command == "subscribe"):
          await self.subscribe(websocket, symbol)
        elif (command == "unsubscribe"):
          await self.unsubscribe(websocket, symbol)
    except websockets.exceptions.WebSocketException as e:
      await self.removeSubscriber(websocket)
      self.logger.error(f"TikkaServer: {type(e)}")
      self.logger.exception(e)
      raise e
      
    await self.removeSubscriber(websocket)

  async def addSubscriber(self, websocket):
    self.subscribers[websocket] = set()

  async def removeSubscriber(self, websocket):
    self.logger.debug("TikkaServer: removeSubscriber")
    symbols = self.subscribers.get(websocket, [])
    while (len(symbols) > 0):
      symbol = symbols.pop()
      await self.unsubscribe(websocket, symbol)
    self.subscribers.pop(websocket, None) # remove key

  async def subscribe(self, websocket, symbol):
    self.logger.debug(f"TikkaServer.subscribe({symbol})")
    self.logger.debug(f"len(subscriptions) == {len(self.subscriptions)}")
    if (len(self.subscriptions) >= MAX_SYMBOLS):
      self.logger.debug("MAX_SYMBOLS reached!")
      await websocket.send(self.maxSymbolsEvent())
      return
    
    self.subscribers[websocket].add(symbol)
    subscribers = self.subscriptions.get(symbol, set())
    subscribers.add(websocket)
    self.subscriptions[symbol] = subscribers
    await self.subscribeOnClient(symbol)

  async def unsubscribe(self, websocket, symbol):
    self.logger.debug(f"TikkaServer.unsubscribe({symbol})")
    self.subscribers[websocket].discard(symbol)
    subscribers = self.subscriptions.get(symbol, None)
    if (subscribers):
      subscribers.remove(websocket)
      if (len(subscribers) == 0):
        await self.unsubscribeOnClient(symbol)

  async def subscribeOnClient(self, symbol):
    if (self.clientInstance):
      await self.clientInstance.subscribe(symbol)
    else:
      self.logger.error("tikka server missing reference to FinnHub client")

  async def unsubscribeOnClient(self, symbol):
    if (self.clientInstance):
      await self.clientInstance.unsubscribe(symbol)
    else:
      self.logger.error("tikka server missing reference to FinnHub client")

  async def updatePrice(self, symbol, price):
    self.logger.debug(f"TikkaServer.updatePrice({symbol}, {price})")
    event = self.updatePriceEvent(symbol, price)
    for subscriber in self.subscriptions.get(symbol, []):
      try:
        await subscriber.send(event)
      except websockets.exceptions.ConnectionClosed:
        self.logger.warning("tried to update a closed connection!")

  def updatePriceEvent(self, symbol, price):
    return json.dumps({"data": [{"s": symbol, "p": price, "v": "0.01", "t": datetime.datetime.utcnow().strftime("%s")}], "type": "trade"})

  def maxSymbolsEvent(self):
    return json.dumps({"data": "The system is at maximum capacity.  Please try again later.", "type": "error"})


async def moreThanOne(*awaitables):
  await asyncio.gather(*awaitables)


def main(certfile, keyfile, port):
  """
  Run client and server on a single asyncio event loop.
  This way they both live in the same process, and can pass messages via method calls.
  """

  logging.basicConfig(filename='tikka.log', level=logging.DEBUG, format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
  logger = logging.getLogger('websockets')
  logger.setLevel(logging.ERROR)
  logger.addHandler(logging.StreamHandler())

  finnhub_client = FinnhubClient()
  tikka_server = TikkaServer()
  finnhub_client.setServerInstance(tikka_server)
  tikka_server.setClientInstance(finnhub_client)

  client_task = finnhub_client.run()
  server_task = None

  if (certfile and keyfile):
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile, keyfile=keyfile)
    server_task = websockets.serve(tikka_server.run, "localhost", port, ssl=ssl_context)
  else:
    server_task = websockets.serve(tikka_server.run, "localhost", port)

  logger = logging.getLogger('dlove.it.Tikka')
  logger.info("Starting server.")
  #asyncio.get_event_loop().set_debug(True)
  asyncio.get_event_loop().run_until_complete(moreThanOne(client_task, server_task))
  asyncio.get_event_loop().run_forever()
