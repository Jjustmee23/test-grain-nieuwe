import os
import django
import pandas as pd
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mill.models import Batch, Factory, City
from mill.views.batch_import_views import (
    validate_excel_data, 
    find_best_factory_match, 
    get_factory_for_import,
    process_batch_row
)

def test_nineveh_import():
    """Test the Nineveh Excel import functionality"""
    print("=== TESTING NINEEVEH BATCH IMPORT ===")
    
    # Read the Excel file
    df = pd.read_excel('نينوى.xlsx')
    print(f"Excel file loaded: {df.shape}")
    
    # Validate data
    try:
        df_clean = validate_excel_data(df)
        print(f"✅ Data validation successful: {df_clean.shape}")
        print(f"Columns: {list(df_clean.columns)}")
    except Exception as e:
        print(f"❌ Data validation failed: {str(e)}")
        return
    
    # Test factory matching
    print("\n=== FACTORY MATCHING TEST ===")
    all_factories = Factory.objects.filter(status=True)
    mosul_factories = all_factories.filter(city__name__icontains='موصل')
    
    print(f"Total factories: {all_factories.count()}")
    print(f"Mosul factories: {mosul_factories.count()}")
    
    # Test first few rows
    test_rows = df_clean.head(5)
    matches_found = 0
    matches_not_found = 0
    
    for idx, row in test_rows.iterrows():
        mill_name = row['mill_name']
        print(f"\nTesting: {mill_name}")
        
        # Test auto-detect matching
        factory = get_factory_for_import(mill_name, 'auto', None, None)
        
        if factory:
            print(f"✅ Match found: {factory.name} (City: {factory.city.name})")
            matches_found += 1
        else:
            print(f"❌ No match found")
            matches_not_found += 1
    
    print(f"\n=== MATCHING SUMMARY ===")
    print(f"✅ Matches found: {matches_found}")
    print(f"❌ No matches: {matches_not_found}")
    print(f"📊 Success rate: {matches_found/(matches_found+matches_not_found)*100:.1f}%")
    
    # Test batch creation simulation
    print(f"\n=== BATCH CREATION SIMULATION ===")
    total_grains = 0
    batches_to_create = 0
    
    for idx, row in df_clean.iterrows():
        mill_name = row['mill_name']
        net_grains = row['net_grains']
        factory = get_factory_for_import(mill_name, 'auto', None, None)
        
        if factory:
            total_grains += net_grains
            batches_to_create += 1
            print(f"📦 {mill_name} → {factory.name} ({net_grains} tons)")
    
    print(f"\n=== SIMULATION RESULTS ===")
    print(f"📦 Total batches to create: {batches_to_create}")
    print(f"🌾 Total grains: {total_grains:,.0f} tons")
    print(f"📊 Average per batch: {total_grains/batches_to_create:,.0f} tons")
    
    return {
        'total_rows': len(df_clean),
        'matches_found': matches_found,
        'matches_not_found': matches_not_found,
        'batches_to_create': batches_to_create,
        'total_grains': total_grains
    }

def test_multiple_files():
    """Test multiple file import functionality"""
    print("\n=== TESTING MULTIPLE FILES IMPORT ===")
    
    # Create a test file for Baghdad
    baghdad_data = {
        'ت': [1, 2, 3],
        'اسم المطحنة': ['بغداد', 'الكرخ', 'الرصافة'],
        'الطاقة التصميمية': [400, 300, 250],
        'صافي الحبوب': [2000, 1500, 1200]
    }
    
    baghdad_df = pd.DataFrame(baghdad_data)
    baghdad_df.to_excel('test_baghdad.xlsx', index=False)
    print("✅ Created test Baghdad file")
    
    # Test both files
    files = ['نينوى.xlsx', 'test_baghdad.xlsx']
    total_results = {}
    
    for file in files:
        if os.path.exists(file):
            print(f"\n--- Testing {file} ---")
            df = pd.read_excel(file)
            df_clean = validate_excel_data(df)
            
            file_results = {
                'rows': len(df_clean),
                'grains': df_clean['net_grains'].sum(),
                'mills': len(df_clean['mill_name'].unique())
            }
            
            total_results[file] = file_results
            print(f"📄 {file}: {file_results['rows']} rows, {file_results['grains']:,.0f} tons")
    
    print(f"\n=== MULTIPLE FILES SUMMARY ===")
    total_rows = sum(r['rows'] for r in total_results.values())
    total_grains = sum(r['grains'] for r in total_results.values())
    print(f"📁 Files: {len(files)}")
    print(f"📊 Total rows: {total_rows}")
    print(f"🌾 Total grains: {total_grains:,.0f} tons")
    
    # Cleanup
    if os.path.exists('test_baghdad.xlsx'):
        os.remove('test_baghdad.xlsx')
        print("✅ Cleaned up test file")

if __name__ == "__main__":
    # Test Nineveh import
    nineveh_results = test_nineveh_import()
    
    # Test multiple files
    test_multiple_files()
    
    print(f"\n🎯 ALL TESTS COMPLETED!")
    print(f"Ready for production import!") 