function set_charts(website_views_labels, website_views, entrys_exits_labels, entrys_count, exits_count) {
    var ctx1 = document.getElementById("entrys-exits__chart").getContext("2d");

    var greenGradient = ctx1.createLinearGradient(0, 230, 0, 50);
    greenGradient.addColorStop(1, 'rgba(31, 224, 116, 0.175)');
    greenGradient.addColorStop(0.2, 'rgba(31, 224, 116, 0.0)');
    greenGradient.addColorStop(0, 'rgba(31, 224, 116, 0)');
  
    var redGradient = ctx1.createLinearGradient(0, 230, 0, 50);
    redGradient.addColorStop(1, 'rgba(250, 77, 86, 0.175)');
    redGradient.addColorStop(0.2, 'rgba(250, 77, 86, 0.0)');
    redGradient.addColorStop(0, 'rgba(250, 77, 86, 0)');
    chart = new Chart(ctx1, {
      type: "line",
      data: {
        labels: entrys_exits_labels,
        datasets: [
            {
              label: "Entrys",
              tension: 0.4,
              borderWidth: 0,
              pointRadius: 0,
              borderColor: "#1fe074",
              backgroundColor: greenGradient,
              borderWidth: 3,
              fill: true,
              data: entrys_count,
              maxBarThickness: 6,
            },
            {
              label: "Exits",
              tension: 0.4,
              borderWidth: 0,
              pointRadius: 0,
              borderColor: "#fa4d56",
              backgroundColor: redGradient,
              borderWidth: 3,
              fill: true,
              data: exits_count,
              maxBarThickness: 6,
            }
          ],
      },
      options: {
        onClick: show_entry_exits,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "bottom",
            labels: {
              color: '#777',
              font: {
                size: 11,
                family: "Open Sans",
                style: 'normal',
                lineHeight: 2
              }
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'index',
        },
        scales: {
          y: {
            grid: {
              drawBorder: false,
              display: true,
              drawOnChartArea: true,
              drawTicks: false,
              borderDash: [5, 5]
            },
            ticks: {
              display: true,
              padding: 10,
              color: '#ccc',
              font: {
                size: 11,
                family: "Open Sans",
                style: 'normal',
                lineHeight: 2
              },
            }
          },
          x: {
            grid: {
              drawBorder: false,
              display: false,
              drawOnChartArea: true,
              drawTicks: false,
              borderDash: [5, 5]
            },
            ticks: {
              display: true,
              color: '#ccc',
              padding: 20,
              font: {
                size: 11,
                family: "Open Sans",
                style: 'normal',
                lineHeight: 2
              },
            }
          },
        },
      },
    });
    
    
    
    var ctx2 = document.getElementById("website-views__chart").getContext("2d");

    var blueGradient = ctx2.createLinearGradient(0, 230, 0, 50);
    blueGradient.addColorStop(1, 'rgba(94, 114, 228, 0.2)');
    blueGradient.addColorStop(0.2, 'rgba(94, 114, 228, 0.0)');
    blueGradient.addColorStop(0, 'rgba(94, 114, 228, 0)');
    new Chart(ctx2, {
      type: "line",
      data: {
        labels: website_views_labels,
        datasets: [{
            label: "Website logins",
            tension: 0.4,
            borderWidth: 0,
            pointRadius: 0,
            borderColor: "#5e72e4",
            backgroundColor: blueGradient,
            borderWidth: 3,
            fill: true,
            data: website_views,
            maxBarThickness: 6,
          }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        interaction: {
          intersect: false,
          mode: 'index',
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              drawBorder: false,
              display: true,
              drawOnChartArea: true,
              drawTicks: false,
              borderDash: [5, 5]
            },
            ticks: {
              display: true,
              padding: 10,
              color: '#ccc',
              font: {
                size: 11,
                family: "Open Sans",
                style: 'normal',
                lineHeight: 2
              },
            }
          },
          x: {
            grid: {
              drawBorder: false,
              display: false,
              drawOnChartArea: false,
              drawTicks: false,
              borderDash: [5, 5]
            },
            ticks: {
              display: true,
              color: '#ccc',
              padding: 20,
              font: {
                size: 11,
                family: "Open Sans",
                style: 'normal',
                lineHeight: 2
              },
            }
          },
        },
      },
    });
}