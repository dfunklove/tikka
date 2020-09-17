var max_samples = 10000;
var values = [];
var charts = [];

function initialize() {
  charts.push(new Chart(document.getElementById("chart0"), {
    type: 'line',
    data: {
      //labels: labels,
      datasets: [{
        data: values,
        backgroundColor: 'rgba(255, 99, 132, 0.1)',
        borderColor: 'rgb(255, 99, 132)',
        borderWidth: 2,
        lineTension: 0.25,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true,
      animation: {
        duration: 420,
        easing: 'linear'
      },
      legend: false,
      scales: {
        xAxes: [{
          type: "time",
          display: true
        }],
        yAxes: [{
          type: "linear"
        }]
      }
    }
  }))
}

function updateCharts(){
  charts.forEach(function(chart) {
    chart.update();
  });
}

currentPrice = 0

function addValue(price) {
  currentPrice = price
  setTimeout(function() {
    requestAnimationFrame(addValueDeferred)
  }, 0)
}

function addValueDeferred() {
  console.log("currentPrice="+currentPrice)
  values.push({
    x: new Date(),
    y: currentPrice
  });
  if (values.length > max_samples)
    values.shift()
  updateCharts()
}

window.onload = function() {
  initialize();
};
