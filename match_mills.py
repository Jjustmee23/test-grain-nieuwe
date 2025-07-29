import os
import django
import pandas as pd
from difflib import SequenceMatcher

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mill.models import Factory, City

def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_match(mill_name, factories):
    """Find the best matching factory for a mill name"""
    best_match = None
    best_score = 0
    
    for factory in factories:
        # Exact match
        if factory.name == mill_name:
            return factory, 1.0
        
        # Calculate similarity
        score = similarity(factory.name, mill_name)
        if score > best_score:
            best_score = score
            best_match = factory
    
    return best_match, best_score

# Read Excel file
df = pd.read_excel('نينوى.xlsx')

# Extract mill names from Excel
excel_mills = []
for idx, row in df.iterrows():
    mill_name = row.iloc[18]  # Column 18 (mill name)
    if pd.notna(mill_name) and str(mill_name).strip() and str(mill_name) != 'اسم المطحنة':
        serial = row.iloc[21]  # Column 21 (serial number)
        capacity = row.iloc[16]  # Column 16 (capacity)
        net_grains = row.iloc[12]  # Column 12 (net grains)
        
        if pd.notna(serial) and pd.notna(capacity) and pd.notna(net_grains):
            excel_mills.append({
                'serial': serial,
                'mill_name': str(mill_name).strip(),
                'capacity': capacity,
                'net_grains': net_grains
            })

# Get all factories from system
factories = Factory.objects.filter(status=True)

print("=== MILL MATCHING ANALYSE ===")
print(f"Excel mills: {len(excel_mills)}")
print(f"Systeem factories: {factories.count()}")
print()

# Find Mosul factories specifically
mosul_factories = factories.filter(city__name__icontains='موصل')
print(f"Mosul factories in systeem: {mosul_factories.count()}")
print()

print("=== MATCHING RESULTATEN ===")
print("┌─────────┬──────────────────────────────┬──────────────────────────────┬──────────┬──────────────┐")
print("│ Excel   │ Excel Mill Name              │ Systeem Factory              │ Match    │ Similarity   │")
print("├─────────┼──────────────────────────────┼──────────────────────────────┼──────────┼──────────────┤")

exact_matches = 0
partial_matches = 0
no_matches = 0

for excel_mill in excel_mills:
    mill_name = excel_mill['mill_name']
    
    # First try to find in Mosul factories
    best_match, score = find_best_match(mill_name, mosul_factories)
    
    if best_match:
        if score == 1.0:
            match_type = "EXACT"
            exact_matches += 1
        elif score > 0.7:
            match_type = "GOOD"
            partial_matches += 1
        else:
            match_type = "WEAK"
            partial_matches += 1
    else:
        # Try in all factories
        best_match, score = find_best_match(mill_name, factories)
        if best_match and score > 0.7:
            match_type = "OTHER"
            partial_matches += 1
        else:
            match_type = "NONE"
            no_matches += 1
            best_match = None
            score = 0
    
    # Format for display
    excel_name = mill_name[:28] + "..." if len(mill_name) > 28 else mill_name.ljust(28)
    sys_name = best_match.name[:28] + "..." if best_match and len(best_match.name) > 28 else (best_match.name.ljust(28) if best_match else "N/A".ljust(28))
    
    print(f"│ {excel_mill['serial']:7.0f} │ {excel_name} │ {sys_name} │ {match_type:8} │ {score:10.2f} │")

print("└─────────┴──────────────────────────────┴──────────────────────────────┴──────────┴──────────────┘")

print()
print("=== SAMENVATTING ===")
print(f"✅ Exact matches: {exact_matches}")
print(f"🔄 Partial matches: {partial_matches}")
print(f"❌ No matches: {no_matches}")
print(f"📊 Total: {len(excel_mills)}")
print()
print(f"🎯 Match percentage: {((exact_matches + partial_matches) / len(excel_mills) * 100):.1f}%")

print()
print("=== EXACT MATCHES ===")
for excel_mill in excel_mills:
    mill_name = excel_mill['mill_name']
    best_match, score = find_best_match(mill_name, mosul_factories)
    if best_match and score == 1.0:
        print(f"✅ {mill_name} → {best_match.name}")

print()
print("=== NO MATCHES ===")
for excel_mill in excel_mills:
    mill_name = excel_mill['mill_name']
    best_match, score = find_best_match(mill_name, factories)
    if not best_match or score < 0.5:
        print(f"❌ {mill_name} → Geen match gevonden") 