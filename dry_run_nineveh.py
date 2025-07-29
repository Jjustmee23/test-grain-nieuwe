import pandas as pd
from datetime import datetime, date

# Read the Excel file
df = pd.read_excel('نينوى.xlsx')

print("=== DRY RUN: NINEEVEH BATCH CREATIE ===")
print(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Excel File: نينوى.xlsx")
print()

# Find the data rows
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

print(f"Totaal mills gevonden: {len(data_rows)}")
print(f"Totaal graan: {sum(row['net_grains'] for row in data_rows):,.0f} tons")
print()

# Simulate batch creation
current_date = date.today()
batch_counter = 1

print("=== VOORSTEL BATCH CREATIE ===")
print("Format: {FACTORY_NAME}_{DATE}_{SEQUENCE}")
print()

print("┌─────────┬──────────────────────────────┬──────────────┬──────────────┬─────────────────────────────┐")
print("│ Batch # │ Factory Name                 │ Net Grains   │ Capacity     │ Batch Number                │")
print("├─────────┼──────────────────────────────┼──────────────┼──────────────┼─────────────────────────────┤")

for row in data_rows:
    mill_name = str(row['mill_name']).strip()
    net_grains = row['net_grains']
    capacity = row['capacity']
    
    # Generate batch number
    batch_number = f"{mill_name}_{current_date.strftime('%Y%m%d')}_{batch_counter:03d}"
    
    # Format for display
    print(f"│ {batch_counter:7d} │ {mill_name:28} │ {net_grains:10,.0f} │ {capacity:10,.0f} │ {batch_number:27} │")
    
    batch_counter += 1

print("└─────────┴──────────────────────────────┴──────────────┴──────────────┴─────────────────────────────┘")

print()
print("=== SAMENVATTING ===")
print(f"✅ Totaal batches te maken: {len(data_rows)}")
print(f"✅ Totaal graan volume: {sum(row['net_grains'] for row in data_rows):,.0f} tons")
print(f"✅ Gemiddelde per batch: {sum(row['net_grains'] for row in data_rows)/len(data_rows):,.0f} tons")
print(f"✅ Stad: Nineveh (نينوى)")
print(f"✅ Start datum: {current_date}")
print()

print("=== FACTORY MATCHING STRATEGIE ===")
print("1. Zoek factory op naam (exact match)")
print("2. Zoek factory op naam (partial match)")
print("3. Zoek factory op naam (fuzzy match)")
print("4. Als niet gevonden: maak nieuwe factory aan")
print()

print("=== VOORBEELD MATCHING ===")
sample_mills = data_rows[:5]
for row in sample_mills:
    mill_name = str(row['mill_name']).strip()
    print(f"🔍 '{mill_name}' → Zoek in systeem...")

print()
print("=== VOLGENDE STAPPEN ===")
print("1. ✅ Excel file geanalyseerd")
print("2. 🔄 Factory matching implementeren")
print("3. 🔄 Batch creatie logica implementeren")
print("4. 🔄 Import functionaliteit testen")
print("5. 🚀 Productie implementatie") 