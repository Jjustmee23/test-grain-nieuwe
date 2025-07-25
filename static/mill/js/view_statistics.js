let factoryId = 1;
const selectedDate = new Date().toLocaleDateString();
const initialDailyLabels = [];
const initialDailyData = [];
const initialMonthlyLabels = [];
const initialMonthlyData = [];
const initialYearlyCurrent = 0;
const initialYearlyPrevious = 0;
const initialHourlyLabels = Array(24).fill().map((_, i) => `${i.toString().padStart(2, '0')}:00`);
const initialHourlyData = [];

document.addEventListener('DOMContentLoaded', () => {
    factoryId = document.getElementById('factoryId').value;
    initializeCharts();
    
    // Auto-select device logic: if only one device, select it; if multiple devices, default to 'all'
    const deviceSelector = document.getElementById('deviceSelector');
    if (deviceSelector) {
        const deviceOptions = deviceSelector.options;
        const deviceCount = deviceOptions.length - 1; // Subtract 1 for "All Devices" option
        
        if (deviceCount === 1) {
            // If only one device, select it automatically
            deviceSelector.value = deviceOptions[1].value; // Index 1 is the first actual device
        } else {
            // If multiple devices, default to 'all'
            deviceSelector.value = 'all';
        }
    }
    
    fetchChartData();
});

function refreshCharts() {
    updateDeviceInfo();
    fetchChartData();
}

function updateDeviceInfo() {
    const deviceSelector = document.getElementById('deviceSelector');
    const selectedDeviceName = document.getElementById('selectedDeviceName');
    
    if (deviceSelector && selectedDeviceName) {
        const selectedOption = deviceSelector.options[deviceSelector.selectedIndex];
        selectedDeviceName.textContent = selectedOption.text;
    }
}

function initializeCharts() {
    // Hourly Chart
    const hourlyCanvas = document.getElementById('hourlyChart');
    if (!hourlyCanvas) {
        console.warn('hourlyChart canvas not found');
        return;
    }
    const hourlyCtx = hourlyCanvas.getContext('2d');
    if (!hourlyCtx) {
        console.warn('hourlyChart context not available');
        return;
    }
    window.hourlyChart = new Chart(hourlyCtx, {
        type: 'bar',
        data: {
            labels: initialHourlyLabels,
            datasets: [{
                label: 'Hourly Production',
                data: initialHourlyData,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: { display: true, text: 'Hour' }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Production (Units)' }
                }
            }
        }
    });

    // Daily Chart
    const dailyCanvas = document.getElementById('dailyChart');
    if (!dailyCanvas) {
        console.warn('dailyChart canvas not found');
        return;
    }
    const dailyCtx = dailyCanvas.getContext('2d');
    if (!dailyCtx) {
        console.warn('dailyChart context not available');
        return;
    }
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

    // Monthly Chart
    const monthlyCanvas = document.getElementById('monthlyChart');
    if (!monthlyCanvas) {
        console.warn('monthlyChart canvas not found');
        return;
    }
    const monthlyCtx = monthlyCanvas.getContext('2d');
    if (!monthlyCtx) {
        console.warn('monthlyChart context not available');
        return;
    }
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

    // Yearly Chart
    const yearlyCanvas = document.getElementById('yearlyChart');
    if (!yearlyCanvas) {
        console.warn('yearlyChart canvas not found');
        return;
    }
    const yearlyCtx = yearlyCanvas.getContext('2d');
    if (!yearlyCtx) {
        console.warn('yearlyChart context not available');
        return;
    }
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
    const deviceId = document.getElementById('deviceSelector') ? document.getElementById('deviceSelector').value : 'all';

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

    // Use the new device-specific API endpoint
    const apiUrl = deviceId === 'all' 
        ? `/api/chart_data?factory_id=${factoryId}&date=${date}`
        : `/api/device-chart-data/${factoryId}/?date=${date}&device_id=${deviceId}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                alert(`Fout: ${data.error}`);
                return;
            }

            // Update Hourly Chart
            if (window.hourlyChart && data.hourly_labels && data.hourly_data) {
                window.hourlyChart.data.labels = data.hourly_labels;
                window.hourlyChart.data.datasets[0].data = data.hourly_data;
                window.hourlyChart.update();
            }

            // Update Daily Chart
            if (window.dailyChart && data.daily_labels && data.daily_data) {
                window.dailyChart.data.labels = data.daily_labels;
                window.dailyChart.data.datasets[0].data = data.daily_data;
                window.dailyChart.update();
            }

            // Update Monthly Chart
            if (window.monthlyChart && data.monthly_labels && data.monthly_data) {
                window.monthlyChart.data.labels = data.monthly_labels;
                window.monthlyChart.data.datasets[0].data = data.monthly_data;
                window.monthlyChart.update();
            }

            // Update Yearly Chart
            if (window.yearlyChart && typeof data.yearly_current !== "undefined" && typeof data.yearly_previous !== "undefined") {
                window.yearlyChart.data.datasets[0].data = [data.yearly_current, data.yearly_previous];
                window.yearlyChart.update();
            }

            updateCommulative(
                data.daily_total,
                data.weekly_total,
                data.monthly_total,
                data.yearly_current,
                data.yearly_previous
            );
        })
        .catch(error => {
            console.error('Error fetching chart data:', error);
            alert('Fout bij het ophalen van grafiekgegevens.');
        });
}

function updateCommulative(daily_data, weekly_data, monthly_data, yearly_data, previous_data) {
    let daily = document.getElementById('total-daily');
    let weekly = document.getElementById('total-week');
    let yearly = document.getElementById('total-year');
    let previously = document.getElementById('total-previous');
    
    if (daily) daily.innerHTML = daily_data;
    if (weekly) weekly.innerHTML = weekly_data;
    if (yearly) yearly.innerHTML = yearly_data;
    if (previously) previously.innerHTML = previous_data;
}
