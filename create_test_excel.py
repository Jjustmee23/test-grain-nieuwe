import pandas as pd

# Test data
data = {
    'Mill Name': ['Buri Mill', 'Mosul Mill', 'Al-Hasad Mill', 'Al-Jazeera Mill', 'Sinjar Mill'],
    'Capacity': [400, 300, 250, 200, 150],
    'Net Grains': [2853, 1544, 1207, 1025, 772],
    'Date': ['2025-03-23', '2025-03-23', '2025-03-23', '2025-03-23', '2025-03-23'],
    'Batch Number': ['BURI_20250323_001', 'MOSUL_20250323_001', 'HASAD_20250323_001', 'JAZEERA_20250323_001', 'SINJAR_20250323_001']
}

# Create DataFrame
df = pd.DataFrame(data)

# Save as Excel file
df.to_excel('test_batch_import.xlsx', index=False)

print("Test Excel file created: test_batch_import.xlsx") 