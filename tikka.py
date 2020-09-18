import asyncio
import websockets
import datetime
import json
import logging
import traceback

class FinnhubClient:
  URI = "wss://ws.finnhub.io?token=bqq9i0nrh5r9ffdhino0"

  def __init__(self, setServerInstance=None):
    self.serverInstance = setServerInstance
    self.websocket = None
    self.subscriptions = set()

  def setServerInstance(self, serverInstance):
    self.serverInstance = serverInstance

  async def run(self):
    while True:
      try:
        print("Connecting to FinnHub...")
        async with websockets.connect(FinnhubClient.URI) as websocket:
          self.websocket = websocket
          self.subscriptions = set()
          print("Connected.")
          await listen_forever(websocket, self)
      except (ConnectionRefusedError, websockets.exceptions.WebSocketException) as e:
          print(f"FinnhubClient: {type(e)}")
          print(e)
          traceback.print_tb(e.__traceback__)
          await asyncio.sleep(5)
          continue

  async def on_message(self, message, websocket):
    print(f"< {message}")
    message = json.loads(message)
    if (message.get('type', None) == 'trade'):
      symbol = message['data'][-1]['s']
      price = message['data'][-1]['p']
      await self.updateOnServer(symbol, price)

  async def updateOnServer(self, symbol, price):
    await self.serverInstance.updatePrice(symbol, price)

  async def subscribe(self, symbol):
    print(f"FinnhubClient.subscribe({symbol})")
    if symbol not in self.subscriptions:
      self.subscriptions.add(symbol)
      event = self.subscribeEvent(symbol)
      print(f"event: {event}")
      await self.websocket.send(event)

  def subscribeEvent(self, symbol):
    return json.dumps({"type":"subscribe", "symbol": symbol})


class TikkaServer:
  def __init__(self, clientInstance=None):
    self.clientInstance = clientInstance
    self.subscriptions = {}
    self.subscribers = {}

  def setClientInstance(self, clientInstance):
    self.clientInstance = clientInstance

  async def run(self, websocket, path):
    print("Connection established.")
    await self.addSubscriber(websocket)

    try:
      await listen_forever(websocket, self)
    except websockets.exceptions.WebSocketException as e:
      await self.removeSubscriber(websocket)
      print(f"TikkaServer: {type(e)}")
      print(e)
      raise e

  async def on_message(self, message, websocket):
    print(f"< {message}")

    # get symbol and command (subscribe/unsubscribe) from message
    message = json.loads(message)
    command = message.get('type', None)
    symbol = message.get('symbol', None)

    # call subscribe/unsubscribe on finnhub client
    if (command == "subscribe"):
      await self.subscribe(websocket, symbol)
    elif (command == "unsubscribe"):
      pass # TODO

  async def addSubscriber(self, websocket):
    self.subscribers[websocket] = set()

  async def removeSubscriber(self, websocket):
    print("TikkaServer: removeSubscriber")
    symbols = self.subscribers[websocket]
    for symbol in symbols:
      self.subscriptions[symbol].remove(websocket)
    self.subscribers.pop(websocket, None) # remove key

  async def subscribe(self, websocket, symbol):
    print(f"TikkaServer.subscribe({symbol})")
    self.subscribers[websocket].add(symbol)
    subscribers = self.subscriptions.get(symbol, None)
    if (not subscribers):
      subscribers = set()
    subscribers.add(websocket)
    self.subscriptions[symbol] = subscribers
    await self.subscribeOnClient(symbol)

  async def subscribeOnClient(self, symbol):
    if (self.clientInstance):
      await self.clientInstance.subscribe(symbol)
    else:
      print("tikka server missing reference to FinnHub client")

  async def updatePrice(self, symbol, price):
    print(f"TikkaServer.updatePrice({symbol}, {price})")
    for subscriber in self.subscriptions.get(symbol, []):
      event = self.updatePriceEvent(symbol, price)
      print(f"event: {event}")
      try:
        await subscriber.send(event)
      except websockets.exceptions.ConnectionClosed:
        print("tried to update a closed connection!")

  def updatePriceEvent(self, symbol, price):
    return json.dumps({"data": [{"s": symbol, "p": price, "v": "0.01", "t": datetime.datetime.utcnow().strftime("%s")}], "type": "trade"})


async def listen_forever(websocket, handler_obj):
  while True:
    try:
      message = await asyncio.wait_for(websocket.recv(), timeout=60)
    except asyncio.TimeoutError:
      try:
        pong = await websocket.ping()
        await asyncio.wait_for(pong, timeout=10)
        print('Ping OK, keeping connection alive...')
        continue
      except Exception as e:
        print(type(e))
        print(e)
        traceback.print_tb(e.__traceback__)
        return
    await handler_obj.on_message(message, websocket)

async def moreThanOne(*awaitables):
  await asyncio.gather(*awaitables)

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  logger = logging.getLogger('websockets.server')
  logger.setLevel(logging.ERROR)
  logger.addHandler(logging.StreamHandler())

  finnhub_client = FinnhubClient()
  tikka_server = TikkaServer()
  finnhub_client.setServerInstance(tikka_server)
  tikka_server.setClientInstance(finnhub_client)

  client_task = finnhub_client.run()
  server_task = websockets.serve(tikka_server.run, "localhost", 8765)
  print("Starting server.")
  asyncio.get_event_loop().set_debug(True)
  asyncio.get_event_loop().run_until_complete(moreThanOne(client_task, server_task))
  asyncio.get_event_loop().run_forever()
