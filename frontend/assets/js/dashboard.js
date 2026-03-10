document.addEventListener("DOMContentLoaded", async () => {

    try {

        await requireAuth()

        const data = await api("/roads")

        const roads = data.road_names || []

        const grid = document.getElementById("roads-grid")

        if (roads.length === 0) {

            grid.innerHTML = "<p>No roads configured</p>"

        }

        roads.forEach(road => {

            const card = createRoadCard(road)

            grid.appendChild(card)

            connectRoadWS(road, card)

        })

    } catch (err) {

        console.error(err)

    }

    initChart()

})



function initChart() {

    const ctx = document.getElementById("trafficChart")

    if (!ctx) return

    new Chart(ctx, {

        type: "line",

        data: {

            labels: ["1","2","3","4","5"],

            datasets: [{

                label: "Traffic Density",

                data: [20,30,40,25,50],

                borderColor: "cyan",

                tension: 0.3

            }]

        },

        options: {

            responsive: true,

            plugins: {

                legend: {

                    labels: {

                        color: "white"

                    }

                }

            },

            scales: {

                x: {

                    ticks: { color: "white" }

                },

                y: {

                    ticks: { color: "white" }

                }

            }

        }

    })

}