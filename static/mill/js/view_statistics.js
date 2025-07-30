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

// Debounce mechanism for device switching
let deviceSwitchTimeout;
let isApiCallInProgress = false;

document.addEventListener('DOMContentLoaded', () => {
    // Wait for complete DOM load and ensure all elements are ready
    if (document.readyState === 'loading') {
        // Still loading, wait for DOMContentLoaded
        document.addEventListener('DOMContentLoaded', initializeApp);
    } else {
        // DOM already loaded
        initializeApp();
    }
});

function initializeApp() {
    console.log('📱 Initializing application...');
    
    // Get factory ID
    const factoryIdElement = document.getElementById('factoryId');
    if (!factoryIdElement) {
        console.error('❌ Factory ID element not found');
        return;
    }
    factoryId = factoryIdElement.value;
    
    // Wait extra time to ensure all DOM elements are available
    setTimeout(() => {
        initializeChartsWithValidation();
        
        // Auto-select device logic
        const deviceSelector = document.getElementById('deviceSelector');
        if (deviceSelector) {
            const deviceOptions = deviceSelector.options;
            const deviceCount = deviceOptions.length;
            
            // Check if "All Devices" option exists (indicates multiple devices)
            const hasAllDevicesOption = Array.from(deviceOptions).some(option => option.value === 'all');
            
            if (!hasAllDevicesOption && deviceCount === 1) {
                // If only one device (no "All Devices" option), it's already selected
                console.log('Single device detected, auto-selected');
            } else if (hasAllDevicesOption) {
                // If "All Devices" option exists, always default to 'all' to be consistent with backend
                deviceSelector.value = 'all';
                console.log('Multiple devices or All Devices option available, defaulting to "All Devices"');
            }
        }
        
        // Fetch initial chart data
        setTimeout(fetchChartData, 200);
        
    }, 200); // Extra 200ms delay to ensure everything is ready
}

function initializeChartsWithValidation() {
    console.log('📊 Starting chart initialization with validation...');
    
    // Comprehensive check for all required canvas elements
    const requiredCanvases = ['hourlyChart', 'dailyChart', 'monthlyChart', 'yearlyChart'];
    const missingCanvases = [];
    
    requiredCanvases.forEach(canvasId => {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            missingCanvases.push(canvasId);
        }
    });
    
    if (missingCanvases.length > 0) {
        console.error('❌ Missing canvas elements:', missingCanvases);
        console.log('⏳ Retrying chart initialization in 500ms...');
        setTimeout(initializeChartsWithValidation, 500);
        return;
    }
    
    console.log('✅ All canvas elements found, proceeding with chart initialization');
    initializeCharts();
}

function refreshCharts() {
    // Prevent concurrent calls
    if (isApiCallInProgress) {
        console.log('🔄 Refresh blocked - API call in progress');
        return;
    }
    
    updateDeviceInfo();
    fetchChartData();
}

function handleDeviceChange() {
    // Prevent concurrent calls with debouncing
    if (deviceSwitchTimeout) {
        clearTimeout(deviceSwitchTimeout);
    }
    
    if (isApiCallInProgress) {
        console.log('🔄 Device change blocked - API call in progress');
        return;
    }
    
    // Debounce device changes to prevent rapid API calls
    deviceSwitchTimeout = setTimeout(() => {
        console.log('🔄 Device change triggered');
        updateDeviceInfo();
        fetchChartData();
    }, 300); // 300ms debounce
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
    console.log('📊 Initializing charts...');
    
    // Destroy existing charts if they exist to prevent memory leaks and conflicts
    if (window.hourlyChart && typeof window.hourlyChart.destroy === 'function') {
        try {
            window.hourlyChart.destroy();
            console.log('✅ Hourly chart destroyed');
        } catch (error) {
            console.warn('⚠️ Error destroying hourly chart:', error);
        }
        window.hourlyChart = null;
    }
    
    if (window.dailyChart && typeof window.dailyChart.destroy === 'function') {
        try {
            window.dailyChart.destroy();
            console.log('✅ Daily chart destroyed');
        } catch (error) {
            console.warn('⚠️ Error destroying daily chart:', error);
        }
        window.dailyChart = null;
    }
    
    if (window.monthlyChart && typeof window.monthlyChart.destroy === 'function') {
        try {
            window.monthlyChart.destroy();
            console.log('✅ Monthly chart destroyed');
        } catch (error) {
            console.warn('⚠️ Error destroying monthly chart:', error);
        }
        window.monthlyChart = null;
    }
    
    if (window.yearlyChart && typeof window.yearlyChart.destroy === 'function') {
        try {
            window.yearlyChart.destroy();
            console.log('✅ Yearly chart destroyed');
        } catch (error) {
            console.warn('⚠️ Error destroying yearly chart:', error);
        }
        window.yearlyChart = null;
    }

    // Helper function to safely get canvas context
    function safeGetContext(canvasId, chartType) {
        try {
            const canvas = document.getElementById(canvasId);
            if (!canvas) {
                console.error(`❌ Canvas element '${canvasId}' not found`);
                return null;
            }
            
            if (!(canvas instanceof HTMLCanvasElement)) {
                console.error(`❌ Element '${canvasId}' is not a canvas element`);
                return null;
            }
            
            const ctx = canvas.getContext('2d');
            if (!ctx) {
                console.error(`❌ Could not get 2D context for '${canvasId}'`);
                return null;
            }
            
            console.log(`✅ Successfully got context for ${canvasId}`);
            return { canvas, ctx };
        } catch (error) {
            console.error(`❌ Error getting context for '${canvasId}':`, error);
            return null;
        }
    }

    // Initialize Hourly Chart
    const hourlyResult = safeGetContext('hourlyChart', 'hourly');
    if (hourlyResult) {
        try {
            window.hourlyChart = new Chart(hourlyResult.ctx, {
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
            console.log('✅ Hourly chart initialized successfully');
        } catch (error) {
            console.error('❌ Error creating hourly chart:', error);
        }
    }

    // Initialize Daily Chart
    const dailyResult = safeGetContext('dailyChart', 'daily');
    if (dailyResult) {
        try {
            window.dailyChart = new Chart(dailyResult.ctx, {
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
            console.log('✅ Daily chart initialized successfully');
        } catch (error) {
            console.error('❌ Error creating daily chart:', error);
        }
    }

    // Initialize Monthly Chart
    const monthlyResult = safeGetContext('monthlyChart', 'monthly');
    if (monthlyResult) {
        try {
            window.monthlyChart = new Chart(monthlyResult.ctx, {
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
            console.log('✅ Monthly chart initialized successfully');
        } catch (error) {
            console.error('❌ Error creating monthly chart:', error);
        }
    }

    // Initialize Yearly Chart
    const yearlyResult = safeGetContext('yearlyChart', 'yearly');
    if (yearlyResult) {
        try {
            window.yearlyChart = new Chart(yearlyResult.ctx, {
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
            console.log('✅ Yearly chart initialized successfully');
        } catch (error) {
            console.error('❌ Error creating yearly chart:', error);
        }
    }
    
    console.log('📊 Chart initialization completed');
}

function fetchChartData() {
    // Prevent concurrent API calls
    if (isApiCallInProgress) {
        console.log('🔄 Fetch blocked - API call already in progress');
        return;
    }
    
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

    // Mark API call as in progress
    isApiCallInProgress = true;
    console.log('📡 Starting API call for device:', deviceId);

    // Use the device-specific API endpoint for both 'all' and specific devices to ensure consistency
    const apiUrl = `/api/device-chart-data/${factoryId}/?date=${date}&device_id=${deviceId}`;

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
            
            console.log('✅ API call completed successfully for device:', deviceId);
        })
        .catch(error => {
            console.error('Error fetching chart data:', error);
            alert('Fout bij het ophalen van grafiekgegevens.');
        })
        .finally(() => {
            // Always clear the API call flag
            isApiCallInProgress = false;
            console.log('🔄 API call finished, ready for next request');
        });
}

function updateCommulative(daily_data, weekly_data, monthly_data, yearly_data, previous_data) {
    // Safely update production totals with null checks
    const daily = document.getElementById('total-daily');
    const weekly = document.getElementById('total-week');
    const yearly = document.getElementById('total-year');
    const previously = document.getElementById('total-previous');
    const monthly = document.getElementById('total-month');
    
    if (daily && daily_data !== undefined && daily_data !== null) {
        daily.innerHTML = daily_data;
        console.log('📊 Updated daily total:', daily_data);
    }
    
    if (weekly && weekly_data !== undefined && weekly_data !== null) {
        weekly.innerHTML = weekly_data;
        console.log('📊 Updated weekly total:', weekly_data);
    }
    
    if (monthly && monthly_data !== undefined && monthly_data !== null) {
        monthly.innerHTML = monthly_data;
        console.log('📊 Updated monthly total:', monthly_data);
    }
    
    if (yearly && yearly_data !== undefined && yearly_data !== null) {
        yearly.innerHTML = yearly_data;
        console.log('📊 Updated yearly total:', yearly_data);
    }
    
    if (previously && previous_data !== undefined && previous_data !== null) {
        previously.innerHTML = previous_data;
        console.log('📊 Updated previous year total:', previous_data);
    }
}
