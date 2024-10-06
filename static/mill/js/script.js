document.addEventListener('DOMContentLoaded', function() {
    // Toggle status button functionality
    const toggleButtons = document.querySelectorAll('.toggle-status');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const deviceId = this.dataset.deviceId;
            fetch(`/api/toggle_device_status?device_id=${deviceId}`, { method: 'POST' })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        alert('Status toggled successfully');
                        location.reload(); // Reload to update the UI with the new status
                    } else {
                        alert(`Error toggling status: ${data.error || 'Unknown error'}`);
                    }
                })
                .catch(error => console.error('Error:', error));
        });
    });

    // Date picker functionality
    const datePicker = document.getElementById('datePicker');
    if (datePicker) {
        datePicker.addEventListener('change', function() {
            const selectedDate = this.value;
            const factoryId = document.getElementById('factorySelect').value; // Assuming a select element for factory

            fetch(`/api/factory_statistics/${factoryId}?date=${selectedDate}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    document.querySelector('.current-value').textContent = data.daily_total || 'No data';
                    document.getElementById('total-daily').textContent = data.daily_total || 'No data';
                    document.getElementById('total-week').textContent = data.weekly_total || 'No data';
                    document.getElementById('total-month').textContent = data.monthly_total || 'No data';
                    document.getElementById('total-year-2023').textContent = data.yearly_total || 'No data';
                })
                .catch(error => console.error('Error fetching data:', error));
        });
    }
});
