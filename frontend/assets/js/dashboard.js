/**
 * dashboard.js — Dashboard logic
 * - Load navbar + auth
 * - Fetch road list → create cards → connect WebSocket
 * - Live chart: hiển thị count xe của road đầu tiên theo thời gian
 */

const MAX_CHART_POINTS = 20;
let trafficChart = null;
let chartLabels = [];
let chartCarData = [];
let chartMotoData = [];
let chartRoadName = null;

document.addEventListener("DOMContentLoaded", async () => {

    // 1. Auth + Navbar
    await loadNavbar();

    // 2. Lấy danh sách tuyến đường
    let roads = [];
    try {
        const data = await api("/roads");
        roads = data.road_names || [];
    } catch (err) {
        console.error("Không lấy được danh sách đường:", err);
    }

    // 3. Tạo road cards
    const grid = document.getElementById("roads-grid");
    if (roads.length === 0) {
        grid.innerHTML = `<div class="empty-state">⚠️ Chưa có tuyến đường nào được cấu hình.</div>`;
    } else {
        // Road đầu tiên sẽ hiển thị trên chart
        chartRoadName = roads[0];
        document.getElementById("chart-road-label").textContent = chartRoadName;

        roads.forEach((road) => {
            const card = createRoadCard(road);
            grid.appendChild(card);
            connectRoadWS(road, card, handleInfoForChart);
        });
    }

    // 4. Init Chart
    initChart();
});

/**
 * Callback nhận data từ WebSocket info stream → cập nhật chart
 */
function handleInfoForChart(data, road) {
    // Chỉ lấy data của road đầu tiên để hiển thị chart
    if (road !== chartRoadName) return;
    if (!trafficChart) return;

    const now = fmtTime();
    chartLabels.push(now);
    chartCarData.push(data.count_car ?? 0);
    chartMotoData.push(data.count_motor ?? 0);

    // Giữ tối đa MAX_CHART_POINTS điểm
    if (chartLabels.length > MAX_CHART_POINTS) {
        chartLabels.shift();
        chartCarData.shift();
        chartMotoData.shift();
    }

    trafficChart.update("none"); // "none" = no animation để smooth
}

/**
 * Khởi tạo Chart.js
 */
function initChart() {
    const ctx = document.getElementById("trafficChart");
    if (!ctx) return;

    trafficChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: chartLabels,
            datasets: [
                {
                    label: "Ô tô",
                    data: chartCarData,
                    borderColor: "#38bdf8",
                    backgroundColor: "rgba(56,189,248,0.08)",
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 5,
                    tension: 0.4,
                    fill: true,
                },
                {
                    label: "Xe máy",
                    data: chartMotoData,
                    borderColor: "#818cf8",
                    backgroundColor: "rgba(129,140,248,0.08)",
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 5,
                    tension: 0.4,
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            animation: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: {
                    labels: { color: "#94a3b8", font: { family: "Inter", size: 12 }, boxWidth: 12 },
                },
                tooltip: {
                    backgroundColor: "#0f172a",
                    borderColor: "rgba(56,189,248,0.2)",
                    borderWidth: 1,
                    titleColor: "#38bdf8",
                    bodyColor: "#cbd5e1",
                },
            },
            scales: {
                x: {
                    ticks: { color: "#475569", font: { size: 11 }, maxTicksLimit: 10 },
                    grid: { color: "rgba(255,255,255,0.04)" },
                },
                y: {
                    ticks: { color: "#475569", font: { size: 11 } },
                    grid: { color: "rgba(255,255,255,0.04)" },
                    beginAtZero: true,
                },
            },
        },
    });
}