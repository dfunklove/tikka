var fuse
var socket
var subscription
var subscribeTime = 0
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
      } else if (mydata['type'] == 'error') {
        document.querySelector('.message-area').innerText = mydata['data']
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
  let new_subscription = document.getElementById("symbol_out").value
  if (!new_subscription || new_subscription === subscription) {
    alert("Instructions:\n1. Enter text.\n2. Select an option from the drop-down.")
    return false
  }
  document.getElementById("go").disabled = true
  if (subscription)
    await unsubscribe(subscription)
  try {
    resetChart()
  } catch(err) {
    console.log(err)
  }
  subscription = new_subscription
  subscribeTime = Date.now()
  await subscribe(subscription)
  setTimeout(updateChart, CHART_EMPTY_MSG_TIMEOUT) // Change the empty overlay if needed
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
        input: document.getElementById("symbol_in"),
        fetch: function (text, update) {
          var result = fuse.search(text);
          for (var key in result) {
            result[key] = result[key].item;
            result[key].label = result[key].text;
          }
          update(result);
        },
        onSelect: function (item) {
          this.input.value = item.text;
          let output_el = document.getElementById("symbol_out")
          if (output_el.value != item.value) {
            output_el.value = item.value;
            document.getElementById("go").disabled = false
          }
        }
      });
    });

  await setupWebsocket();

  // focus on the input field for easy access...
  var input = document.getElementById('symbol_in');
  input.focus();
  // ...but if someone wishes to go back in their history, let them!
  document.onkeydown = function(e) {
    if (!e) {
      var e = window.event;
    }
    if (e.key === "Backspace" && !input.value) {
      history.back();
    }
  };

  pollForUpdates();
});
