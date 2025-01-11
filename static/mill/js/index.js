// static/js/index.js

function handleFactoryClick(factoryId) {
    window.location.href = `/view-statistics/${factoryId}/`;
}

function updateDashboard() {
    const date = document.getElementById('dashboardDatePicker').value;
    const cityId = document.getElementById('citySelector').value;

    // Bouw de URL met de geselecteerde parameters
    let url = '/';
    let params = new URLSearchParams();

    if (cityId) {
        params.append('city', cityId);
    }

    if (date) {
        params.append('date', date);
    }

    if ([...params].length > 0) {
        url += '?' + params.toString();
    }

    // Herlaad de pagina met de nieuwe parameters
    window.location.href = url;
}

function filterFactoriesByCity() {
    const selectedCityId = document.getElementById('cityDropdown').value;

    // Get all factory elements
    const factories = document.querySelectorAll('.factory');
    let visibleFactories = 0; // Counter for visible factories

    // Loop through each factory
    factories.forEach(factory => {
        // Get the city_id of the factory (assuming you have this data attribute)
        const factoryCityId = factory.getAttribute('data-city-id');

        if (selectedCityId === "" || factoryCityId === selectedCityId) {
            // Show the factory if city matches or if no city is selected
            factory.style.display = 'block';
            visibleFactories++; // Increment counter for visible factories
        } else {
            // Hide the factory if it doesn't belong to the selected city
            factory.style.display = 'none';
        }
    });

    // Display message if no factories are visible
    const noFactoriesMessage = document.getElementById('noFactoriesMessage');
    if (visibleFactories === 0) {
        noFactoriesMessage.style.display = 'block'; // Show message
    } else {
        noFactoriesMessage.style.display = 'none'; // Hide message
    }
}

// Function to show the popup
function showNoDevicesPopup() {
    document.getElementById('noDevicesPopup').classList.add('active');
}

// Function to close the popup
function closePopup() {
    document.getElementById('noDevicesPopup').classList.remove('active');
}

// Add an event listener to the OK button to close the popup
document.getElementById('closePopupButton').addEventListener('click', closePopup);



function toggleDarkMode() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    if (currentTheme === 'dark') {
        body.removeAttribute('data-theme');
    } else {
        body.setAttribute('data-theme', 'dark');
    }
}
