document.addEventListener('DOMContentLoaded', function () {
    // Initialize the chart
    const ctx = document.getElementById('performanceChart').getContext('2d');
    const performanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5'], // Example labels
            datasets: [{
                label: 'Daily Performance',
                data: [12, 19, 3, 5, 2], // Example data
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
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

    // Add Column Functionality
    document.getElementById('add-column-widget').addEventListener('click', function() {
        const newCardId = `card${Date.now()}`; // Unique ID for the new card
        const newCard = document.createElement('div');
        newCard.className = 'card shadow-sm mb-3';
        newCard.dataset.id = newCardId;

        // Set the content of the new card
        newCard.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <h4 class="card-title">New Column</h4>
                    <button class="btn btn-link remove-card"><i class="mdi mdi-close"></i></button>
                </div>
                <p class="card-text">This is a new column added by the admin.</p>
            </div>
        `;

        // Append the new card to the container
        document.getElementById('data-cards-container').appendChild(newCard);

        // Attach the remove event listener to the new card's remove button
        newCard.querySelector('.remove-card').addEventListener('click', function () {
            newCard.remove();
        });
    });

    // Manage Titles Functionality
    document.getElementById('manage-titles-widget').addEventListener('click', function() {
        const manageTitlesModal = new bootstrap.Modal(document.getElementById('manageTitlesModal'));
        manageTitlesModal.show();
    });

    // Save Titles Functionality
    document.getElementById('saveTitlesButton').addEventListener('click', function() {
        const title1 = document.getElementById('title1').value;
        const title2 = document.getElementById('title2').value;
        console.log("Title 1:", title1);
        console.log("Title 2:", title2);
        // Close the modal after saving
        const manageTitlesModal = bootstrap.Modal.getInstance(document.getElementById('manageTitlesModal'));
        manageTitlesModal.hide();
    });
});
