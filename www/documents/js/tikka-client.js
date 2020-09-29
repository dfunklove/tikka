var fuse
var socket
var subscription
var lastUpdate = 0
var updates = []

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function setupWebsocket() {
  return new Promise(resolve => {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      resolve()
      return
    }

    socket = new WebSocket('wss://'+window.location.hostname+'/tikka/app');

    socket.addEventListener('open', function (event) {
      console.log("connection opened")
      if (subscription)
        subscribe(subscription)
    });
    
    socket.addEventListener('message', function (event) {
      console.log('Message from server ', event.data);
      let mydata = JSON.parse(event.data)
      if (mydata['type'] == 'trade') {
        let symbol = mydata['data'][0]['s']
        let price = mydata['data'][0]['p']
        console.log(`symbol: ${symbol}, price: ${price}`)
        d = new Date()
        t = d.getTime()
        updates.push(price)
      }
    });

    socket.addEventListener('error', delaySetupWebsocket)
    socket.addEventListener('close', delaySetupWebsocket)
    resolve()
  })
}

async function delaySetupWebsocket() {
  return new Promise(async (resolve) => {
    await sleep(1000);
    await setupWebsocket()
    resolve();
  })
}

async function reopenWebsocket() {
  console.log("reopenWebsocket")
  while (true) {
    console.log("socket.readyState="+socket.readyState)
    if (socket.readyState === WebSocket.CLOSING) {
      await sleep(100)
    } else if (socket.readyState === WebSocket.CONNECTING) {
      await sleep(100)
    } else if (socket.readyState === WebSocket.CLOSED) {
      await sleep(1000)
      await setupWebsocket()
    } else {
      break
    }
  }
}

async function sendOverSocket(data) {
  return new Promise(async (resolve) => {
    await reopenWebsocket()
    console.log("send: "+data)
    socket.send(data)
    resolve()
  })
}

async function subscribe(symbol) {
  console.log("subscribe: "+symbol)
  await sendOverSocket(JSON.stringify({'type':'subscribe','symbol': symbol}))
}

async function unsubscribe(symbol) {
  console.log("unsubscribe: "+symbol)
  await sendOverSocket(JSON.stringify({'type':'unsubscribe','symbol': symbol}))
}

async function updateSubscription(e) {
  e.preventDefault()
  if (subscription)
    await unsubscribe(subscription)
  try {
    resetChart()
  } catch(err) {
    console.log(err)
  }
  subscription = document.getElementById("symbol").value
  await subscribe(subscription)
  return false
}

async function pollForUpdates() {
  while (true) {
    price = updates.pop()
    if (price != undefined) {
      updates = []
      addValue(price)
    }
    await sleep(CHART_REFRESH_RATE)
  }
}

window.addEventListener("load", async () => {
  fetch('symbol_list.json')
    .then(response => response.json())
    .then(response => {
      fuse = new Fuse(response, { threshold: "0", ignoreLocation: "true", keys: ["value", "text"] });
      autocomplete({
        input: document.getElementById("symbol"),
        fetch: function (text, update) {
          var result = fuse.search(text);
          for (var key in result) {
            result[key] = result[key].item;
            result[key].label = result[key].text;
          }
          update(result);
        },
        onSelect: function (item) {
          this.input.value = item.value;
        }
      });
    });

  await setupWebsocket();

  pollForUpdates();
});
