import pandas as pd

# Read the Excel file
df = pd.read_excel('نينوى.xlsx')

print("=== NINEEVEH EXCEL ANALYSE ===")
print(f"Shape: {df.shape}")
print()

# Extract mill names from column 18 (Unnamed: 18)
mills = df.iloc[:, 18].dropna()
print(f"=== MILLS IN NINEEVEH.XLSX ===")
print(f"Totaal aantal mill entries: {len(mills)}")
print()

print("=== ALLE MILLS ===")
for i, mill in enumerate(mills, 1):
    print(f"{i:2d}. {mill}")

print()
print("=== UNIEKE MILLS ===")
unique_mills = mills.unique()
print(f"Unieke mills: {len(unique_mills)}")
for i, mill in enumerate(unique_mills, 1):
    print(f"{i:2d}. {mill}")

print()
print("=== VOLLEDIGE DATA ANALYSE ===")

# Find the data rows (where we have mill names)
data_rows = []
for idx, row in df.iterrows():
    mill_name = row.iloc[18]  # Column 18 (mill name)
    if pd.notna(mill_name) and str(mill_name).strip() and str(mill_name) != 'اسم المطحنة':
        serial = row.iloc[21]  # Column 21 (serial number)
        capacity = row.iloc[16]  # Column 16 (capacity)
        net_grains = row.iloc[12]  # Column 12 (net grains)
        
        if pd.notna(serial) and pd.notna(capacity) and pd.notna(net_grains):
            data_rows.append({
                'serial': serial,
                'mill_name': mill_name,
                'capacity': capacity,
                'net_grains': net_grains
            })

print(f"Geldige data rijen: {len(data_rows)}")
print()
print("=== VOLLEDIGE MILL DATA ===")
for row in data_rows:
    print(f"Serial: {row['serial']:2.0f} | Mill: {str(row['mill_name']):20} | Capacity: {row['capacity']:4.0f} | Net Grains: {row['net_grains']:6.0f}")

print()
print("=== SAMENVATTING ===")
total_grains = sum(row['net_grains'] for row in data_rows)
print(f"Totaal aantal mills: {len(data_rows)}")
print(f"Totaal netto graan: {total_grains:,.0f} tons")
print(f"Gemiddelde per mill: {total_grains/len(data_rows):,.0f} tons") 