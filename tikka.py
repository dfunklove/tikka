import asyncio
import websockets
import datetime
import json

class FinnhubClient:
  def __init__(self, setServerInstance=None):
    self.serverInstance = setServerInstance
    self.websocket = None

  def setServerInstance(self, serverInstance):
    self.serverInstance = serverInstance


  async def run(self):
    uri = "wss://ws.finnhub.io?token=bqq9i0nrh5r9ffdhino0"
    async with websockets.connect(uri) as websocket:
      self.websocket = websocket

      #print("subscribing to symbols...")
      #await websocket.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}')
      #await websocket.send('{"type":"subscribe","symbol":"IC MARKETS:1"}')
      #await self.subscribe("IC MARKETS:1")
      #print("done")

      while True:
        update = await websocket.recv()
        print(f"< {update}")

        # get symbol, price from update
        update = json.loads(update)
        if (update.get('type', None) == 'trade'):
          symbol = update['data'][-1]['s']
          price = update['data'][-1]['p']
          await self.updateOnServer(symbol, price)

  async def updateOnServer(self, symbol, price):
    await self.serverInstance.updatePrice(symbol, price)

  async def subscribe(self, symbol):
    print(f"FinnhubClient.subscribe({symbol})")
    event = self.subscribeEvent(symbol)
    print(f"event: {event}")
    await self.websocket.send(event)

  def subscribeEvent(self, symbol):
    return json.dumps({"type":"subscribe", "symbol": symbol})


class TikkaServer:
  def __init__(self, clientInstance=None):
    self.clientInstance = clientInstance
    self.subscriptions = {}

  def setClientInstance(self, clientInstance):
    self.clientInstance = clientInstance

  async def run(self, websocket, path):
    async for message in websocket:
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
  
  async def subscribe(self, websocket, symbol):
    print(f"TikkaServer.subscribe({symbol})")
    clients = self.subscriptions.get(symbol, None)
    if (not clients):
      clients = set()
    clients.add(websocket)
    self.subscriptions[symbol] = clients
    await self.subscribeOnClient(symbol)

  async def subscribeOnClient(self, symbol):
    await self.clientInstance.subscribe(symbol)

  async def updatePrice(self, symbol, price):
    print(f"TikkaServer.updatePrice({symbol}, {price})")
    for subscriber in self.subscriptions.get(symbol, []):
      event = self.updatePriceEvent(symbol, price)
      print(f"event: {event}")
      await subscriber.send(event)

  def updatePriceEvent(self, symbol, price):
    return json.dumps({"s": symbol, "p": price, "v": "0.01", "t": datetime.datetime.utcnow().strftime("%s")})


async def moreThanOne(*awaitables):
  await asyncio.gather(*awaitables)

if __name__ == '__main__':
  finnhub_client = FinnhubClient()
  tikka_server = TikkaServer()
  finnhub_client.setServerInstance(tikka_server)
  tikka_server.setClientInstance(finnhub_client)

  client_task = finnhub_client.run()
  server_task = websockets.serve(tikka_server.run, "localhost", 8765)
  asyncio.get_event_loop().run_until_complete(moreThanOne(client_task, server_task))
  asyncio.get_event_loop().run_forever()
