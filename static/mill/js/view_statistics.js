// static/js/view_statistics.js
        let factoryId = 1;
        const selectedDate = new Date().toLocaleDateString();
        const initialHourlyLabels = Array.from({length: 24}, (_, i) => `${String(i).padStart(2, '0')}:00`);
        const initialHourlyData = Array(24).fill(0).map(() => Math.floor(Math.random() * 100)); // Random initial data
        const initialDailyLabels = []
        const initialDailyData = [];
        const initialMonthlyLabels = [];
        const initialMonthlyData = [];
        const initialYearlyCurrent = 0;
        const initialYearlyPrevious = 0;

document.addEventListener('DOMContentLoaded', () => {
    // Initialiseer de grafieken met de initiële data
    factoryId = document.getElementById('factoryId').value ;
    console.log(factoryId);
    initializeCharts();
    fetchChartData();
});

function refreshCharts() {
    fetchChartData();
}
function generateRandomHourlyData() {
    const baseValue = Math.random() * 50 + 50; // Random base value between 50 and 100
    return Array(24).fill(0).map(() => {
        // Add some variation to the base value
        const variation = Math.random() * 20 - 10; // Random variation between -10 and +10
        return Math.max(0, Math.floor(baseValue + variation));
    });


function initializeCharts() {
    // Dagelijkse Grafiek

    const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
    window.hourlyChart = new Chart(hourlyCtx, {
        type: 'bar',
        data: {
            labels: initialHourlyLabels,
            datasets: [{
                label: 'Hourly Production',
                data: initialHourlyData,
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Hourly Production (Last 24 Hours)',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    position: 'top',
                }
            },
            scales: {
                x: { 
                    title: { 
                        display: true, 
                        text: 'Hour (UTC)',
                        font: {
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    title: { 
                        display: true, 
                        text: 'Production (Units)',
                        font: {
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            tooltips: {
                mode: 'index',
                intersect: false
            }
        }
    });

    const dailyCtx = document.getElementById('dailyChart').getContext('2d');
    window.dailyChart = new Chart(dailyCtx, {
        type: 'bar',
        data: {
            labels: initialDailyLabels,
            datasets: [{
                label: 'Dagelijkse Productie',
                data: initialDailyData,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { 
                    title: { display: true, text: 'Datum' }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Productie (Eenheden)' }
                }
            }
        }
    });

    // Maandelijkse Grafiek
    const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
    window.monthlyChart = new Chart(monthlyCtx, {
        type: 'line',
        data: {
            labels: initialMonthlyLabels,
            datasets: [{
                label: 'Maandelijkse Productie',
                data: initialMonthlyData,
                backgroundColor: 'rgba(153, 102, 255, 0.6)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1,
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { 
                    title: { display: true, text: 'Maand' }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Productie (Eenheden)' }
                }
            }
        }
    });

    // Jaarlijkse Grafiek
    const yearlyCtx = document.getElementById('yearlyChart').getContext('2d');
    window.yearlyChart = new Chart(yearlyCtx, {
        type: 'pie',
        data: {
            labels: ['Huidig Jaar', 'Vorig Jaar'],
            datasets: [{
                label: 'Jaarlijkse Productie',
                data: [initialYearlyCurrent, initialYearlyPrevious],
                backgroundColor: [
                    'rgba(255, 159, 64, 0.6)',
                    'rgba(54, 162, 235, 0.6)'
                ],
                borderColor: [
                    'rgba(255, 159, 64, 1)',
                    'rgba(54, 162, 235, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true
        }
    });
}

function fetchChartData() {
    const date = document.getElementById('datePicker').value;

    if (typeof factoryId === 'undefined' || factoryId === null) {
        console.error('Factory ID is missing.');
        alert('Fabriek niet gevonden');
        return;
    }

    if (!date) {
        console.error('Date is missing.');
        alert('Ongeldige datum');
        return;
    }

    fetch(`/api/chart_data?factory_id=${factoryId}&date=${date}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                alert(`Fout: ${data.error}`);
                return;
            }
            if (window.hourlyChart) {
                const hourlyData = data.hourly_data || generateRandomHourlyData();
                const currentHour = new Date().getUTCHours();
                
                // Rotate the labels array so that current hour is last
                const rotatedLabels = [...initialHourlyLabels.slice(currentHour + 1), 
                                     ...initialHourlyLabels.slice(0, currentHour + 1)];
                
                window.hourlyChart.data.labels = rotatedLabels;
                window.hourlyChart.data.datasets[0].data = hourlyData;
                window.hourlyChart.options.plugins.title.text = 
                    `Hourly Production (Last Updated: ${new Date().toISOString().slice(0, 19).replace('T', ' ')} UTC)`;
                window.hourlyChart.update();
            }

            // Update Dagelijkse Grafiek
            if (window.dailyChart) {
                window.dailyChart.data.labels = data.daily_labels;
                window.dailyChart.data.datasets[0].data = data.daily_data;
                window.dailyChart.update();
            }

            // Update Maandelijkse Grafiek
            if (window.monthlyChart) {
                window.monthlyChart.data.labels = data.monthly_labels;
                window.monthlyChart.data.datasets[0].data = data.monthly_data;
                window.monthlyChart.update();
            }

            // Update Jaarlijkse Grafiek
            if (window.yearlyChart) {
                window.yearlyChart.data.datasets[0].data = [data.yearly_current, data.yearly_previous];
                window.yearlyChart.update();
            }

            updateCommulative(data.daily_total, data.weekly_total, data.monthly_total, data.yearly_current, data.yearly_previous);
        })
        .catch(error => {
            console.error('Error fetching chart data:', error);
            alert('Fout bij het ophalen van grafiekgegevens.');
        });
}

function updateCommulative(daily_data,weekly_data,monthly_data,yearly_data,previous_data){
    let daily = document.getElementById('total-daily');
    let weekly = document.getElementById('total-week');
    let monthly = document.getElementById('total-month');
    let yearly = document.getElementById('total-year');
    let previously = document.getElementById('total-previous');
    daily.innerHTML = daily_data;
    weekly.innerHTML = weekly_data;
    monthly.innerHTML = monthly_data;
    yearly.innerHTML = yearly_data;
    previously.innerHTML = previous_data;
}
