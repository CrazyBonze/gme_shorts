$(document).ready(function () {

        var getetfs = function(chart) {
                $.getJSON("/api/data/etfs").done(function(json) {
                        json.forEach(etf => getshorts(chart, etf));
                });
        };

        var getshorts = function(chart, url) {
                $.getJSON("/api/data/" + url).done(function(json) {
                        chart.data.labels = json.data.map(x => x.tradeReportDate);
                        chart.data.datasets.push({
                                data: json.data.map(x => x.shortParQuantity),
                                label: json.label,
                                borderColor : random_color(),
                                //backgroundColor: 'rgba(0, 0, 0, 0)',
                                fill: false,
                                hidden: chart.data.datasets.length >= 5 ? true : false,
                        });
                        chart.update();
                });
        }

        var defaultLegendClickHandler = Chart.defaults.global.legend.onClick;
        var test = function(e, legendItem) {
                console.log(legendItem);
                defaultLegendClickHandler(e, legendItem);
        };

        var random_color = function() {
                var x = Math.floor(Math.random() * 128);
                var y = Math.floor(Math.random() * 128);
                var z = Math.floor(Math.random() * 128);
                return "rgba(" + x + "," + y + "," + z + ",0.5)";
        };
        var getRandomColor = function() {
                var letters = '0123456789ABCDEF'.split('');
                var color = '#';
                for (var i = 0; i < 6; i++ ) {
                        color += letters[Math.floor(Math.random() * 16)];
                }
                return color;
        }

        var chLine = document.getElementById("chLine");
        var chart = new Chart(chLine, {
                type: 'line',
                data: {
                        datasets: [
                        ]
                },
                options: {
                        title: {
                                display: true,
                                text: "Short Share Volume for ETFs containing GME",
                        },
                        scales: {
                                yAxes: [{
                                        id: 'short_shares',
                                        ticks: {
                                                beginAtZero: false
                                        },
                                        scaleLabel: {
                                                display: true,
                                                labelString: 'Short Volume'
                                        },
                                }],
                        },
                        legend: {
                                display: true,
                        },
                        tooltips: {
                                enabled: true,
                                mode: 'nearest',
                                intersect: false,

                        }
                }
                });

        getetfs(chart);

});
