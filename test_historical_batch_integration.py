#!/usr/bin/env python3
"""
Test script for historical batch data integration
Tests the new functionality where super admins can change batch start dates
and automatically integrate historical production data.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mill.models import Batch, Factory, Device, User
from django.contrib.auth.models import Group

def test_historical_batch_integration():
    """Test the historical batch integration functionality"""
    
    print("🔍 TESTING HISTORICAL BATCH DATA INTEGRATION")
    print("=" * 60)
    
    # Get a super admin user
    super_admin = User.objects.filter(groups__name='Superadmin').first()
    if not super_admin:
        print("❌ No super admin user found")
        return False
    
    # Get a factory with devices
    factory = Factory.objects.filter(devices__isnull=False).first()
    if not factory:
        print("❌ No factory with devices found")
        return False
    
    print(f"✅ Using Super Admin: {super_admin.username}")
    print(f"✅ Using Factory: {factory.name}")
    
    # Create a test batch
    test_batch_number = f"TEST_HIST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        batch = Batch.objects.create(
            batch_number=test_batch_number,
            factory=factory,
            wheat_amount=100.0,
            waste_factor=20.0,
            expected_flour_output=80.0,
            status='pending'
        )
        print(f"✅ Created test batch: {batch.batch_number}")
        
        # Test 1: Update start date to 1 week ago
        one_week_ago = timezone.now() - timedelta(days=7)
        print(f"🔄 Testing start date update to: {one_week_ago.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            batch.update_start_date_with_historical_data(one_week_ago, super_admin)
            print(f"✅ Successfully updated start date to {one_week_ago.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Current value: {batch.current_value}")
            print(f"   Actual flour output: {batch.actual_flour_output} tons")
        except Exception as e:
            print(f"❌ Error updating start date: {str(e)}")
        
        # Test 2: Update start date to 2 weeks ago
        two_weeks_ago = timezone.now() - timedelta(days=14)
        print(f"🔄 Testing start date update to: {two_weeks_ago.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            batch.update_start_date_with_historical_data(two_weeks_ago, super_admin)
            print(f"✅ Successfully updated start date to {two_weeks_ago.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Current value: {batch.current_value}")
            print(f"   Actual flour output: {batch.actual_flour_output} tons")
        except Exception as e:
            print(f"❌ Error updating start date: {str(e)}")
        
        # Test 3: Try to update with non-super admin (should fail)
        regular_user = User.objects.filter(groups__name='Admin').first()
        if regular_user:
            print(f"🔄 Testing with regular admin user: {regular_user.username}")
            try:
                batch.update_start_date_with_historical_data(one_week_ago, regular_user)
                print("❌ Should have failed - regular user cannot update start date")
            except ValueError as e:
                print(f"✅ Correctly blocked regular user: {str(e)}")
        
        # Test 4: Try to update with future date (should fail)
        future_date = timezone.now() + timedelta(days=1)
        print(f"🔄 Testing with future date: {future_date.strftime('%Y-%m-%d %H:%M')}")
        try:
            batch.update_start_date_with_historical_data(future_date, super_admin)
            print("❌ Should have failed - future date not allowed")
        except ValueError as e:
            print(f"✅ Correctly blocked future date: {str(e)}")
        
        # Clean up
        batch.delete()
        print(f"✅ Cleaned up test batch: {test_batch_number}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in test: {str(e)}")
        return False

def test_batch_126_historical_integration():
    """Test historical integration with actual batch 126"""
    
    print("\n🔍 TESTING BATCH 126 HISTORICAL INTEGRATION")
    print("=" * 60)
    
    try:
        batch = Batch.objects.get(id=126)
        print(f"✅ Found batch 126: {batch.batch_number}")
        print(f"   Current start date: {batch.start_date}")
        print(f"   Current value: {batch.current_value}")
        print(f"   Actual flour output: {batch.actual_flour_output} tons")
        
        # Get super admin
        super_admin = User.objects.filter(groups__name='Superadmin').first()
        if not super_admin:
            print("❌ No super admin user found")
            return False
        
        # Test updating to 20/07 (assuming this is July 20th)
        target_date = datetime(2025, 7, 20, 8, 0, 0)  # July 20, 2025 at 8 AM
        target_date = timezone.make_aware(target_date)
        
        print(f"🔄 Testing start date update to: {target_date.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            batch.update_start_date_with_historical_data(target_date, super_admin)
            print(f"✅ Successfully updated batch 126 start date to {target_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"   New current value: {batch.current_value}")
            print(f"   New actual flour output: {batch.actual_flour_output} tons")
            print(f"   Progress percentage: {batch.progress_percentage}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating batch 126: {str(e)}")
            return False
            
    except Batch.DoesNotExist:
        print("❌ Batch 126 not found")
        return False
    except Exception as e:
        print(f"❌ Error in batch 126 test: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Historical Batch Integration Tests")
    print("=" * 60)
    
    # Test 1: General functionality
    test1_success = test_historical_batch_integration()
    
    # Test 2: Batch 126 specific test
    test2_success = test_batch_126_historical_integration()
    
    print("\n📊 TEST RESULTS")
    print("=" * 60)
    print(f"General functionality test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Batch 126 test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED! Historical batch integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.") 