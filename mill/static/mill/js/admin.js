document.addEventListener('DOMContentLoaded', function () {
    const cityToggleFactorySelect = document.getElementById('city_id_toggle_factory');
    const factoryCheckboxesDiv = document.getElementById('factory-checkboxes');
    const removeCityModal = new bootstrap.Modal(document.getElementById('removeCityModal'));
    const confirmDeleteCityModal = new bootstrap.Modal(document.getElementById('confirmDeleteCityModal'));

    cityToggleFactorySelect.addEventListener('change', function () {
        const cityId = cityToggleFactorySelect.value;
        fetch(`/get_factories_by_city?city_id=${cityId}`)
            .then(response => response.json())
            .then(data => {
                factoryCheckboxesDiv.innerHTML = '';
                if (data.factories) {
                    data.factories.forEach(factory => {
                        const checkbox = document.createElement('input');
                        checkbox.type = 'checkbox';
                        checkbox.name = 'factories';
                        checkbox.value = factory.id;
                        checkbox.checked = factory.status;
                        factoryCheckboxesDiv.appendChild(checkbox);

                        const label = document.createElement('label');
                        label.textContent = factory.name;
                        factoryCheckboxesDiv.appendChild(label);

                        factoryCheckboxesDiv.appendChild(document.createElement('br'));
                    });
                }
            })
            .catch(error => console.error('Error fetching factories:', error));
    });

    document.getElementById('removeCityForm').addEventListener('submit', function (event) {
        event.preventDefault();
        const cityId = document.getElementById('city_id_remove').value;
        fetch(`/get_factories_by_city?city_id=${cityId}`)
            .then(response => response.json())
            .then(data => {
                if (data.factories && data.factories.length > 0) {
                    removeCityModal.hide();
                    document.getElementById('city_id_confirm_remove').value = cityId;
                    confirmDeleteCityModal.show();
                } else {
                    document.getElementById('removeCityForm').submit();
                }
            })
            .catch(error => console.error('Error checking factories:', error));
    });
});
