function openManageColumnsModal(dbName, tableName, columns) {
    console.log("Opening modal for:", dbName, tableName, columns);
    
    document.getElementById('db_name').value = dbName;
    document.getElementById('table_name').value = tableName;

    const columnSelection = document.getElementById('column_selection');
    columnSelection.innerHTML = '';  // Clear any existing content

    columns.forEach(column => {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = 'selected_columns[]';
        checkbox.value = column;
        checkbox.id = `col_${column}`;

        const label = document.createElement('label');
        label.htmlFor = `col_${column}`;
        label.textContent = column;

        const div = document.createElement('div');
        div.className = 'form-check';
        div.appendChild(checkbox);
        div.appendChild(label);

        columnSelection.appendChild(div);
    });

    const modal = new bootstrap.Modal(document.getElementById('manageColumnsModal'));
    modal.show();
}
