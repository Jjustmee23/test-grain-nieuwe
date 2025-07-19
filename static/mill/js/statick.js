// Ensure the DOM is fully loaded before accessing elements
document.addEventListener('DOMContentLoaded', function() {

    // Check if the data is available and correct before initializing charts
    const dailyData = {{ daily_totals | tojson }};
    const weeklyData = {{ weekly_totals | tojson }};
    const monthlyData = {{ monthly_totals | tojson }};
    const yearlyData = {{ yearly_totals | tojson }};

    if (dailyData && weeklyData && monthlyData && yearlyData) {
        
        // Initialize Daily Chart
        const ctxDaily = document.getElementById('dailyChart').getContext('2d');
        const dailyChart = new Chart(ctxDaily, {
            type: 'line',
            data: {
                labels: Array.from({ length: dailyData.length }, (_, i) => `Day ${i + 1}`),
                datasets: [{
                    label: 'Daily Totals',
                    data: dailyData,
                    backgroundColor: 'rgba(52, 152, 219, 0.2)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Initialize Weekly Chart
        const ctxWeekly = document.getElementById('weeklyChart').getContext('2d');
        const weeklyChart = new Chart(ctxWeekly, {
            type: 'line',
            data: {
                labels: Array.from({ length: weeklyData.length }, (_, i) => `Week ${i + 1}`),
                datasets: [{
                    label: 'Weekly Totals',
                    data: weeklyData,
                    backgroundColor: 'rgba(46, 204, 113, 0.2)',
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Initialize Monthly Chart
        const ctxMonthly = document.getElementById('monthlyChart').getContext('2d');
        const monthlyChart = new Chart(ctxMonthly, {
            type: 'line',
            data: {
                labels: Array.from({ length: monthlyData.length }, (_, i) => i + 1),
                datasets: [{
                    label: 'Monthly Totals',
                    data: monthlyData,
                    backgroundColor: 'rgba(241, 196, 15, 0.2)',
                    borderColor: 'rgba(241, 196, 15, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Initialize Yearly Chart
        const ctxYearly = document.getElementById('yearlyChart').getContext('2d');
        const yearlyChart = new Chart(ctxYearly, {
            type: 'line',
            data: {
                labels: Array.from({ length: yearlyData.length }, (_, i) => `Month ${i + 1}`),
                datasets: [{
                    label: 'Yearly Totals',
                    data: yearlyData,
                    backgroundColor: 'rgba(231, 76, 60, 0.2)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

    } else {
        console.error("Chart data is missing or incorrectly formatted.");
    }
});

// Dark mode toggle functionality
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
}
