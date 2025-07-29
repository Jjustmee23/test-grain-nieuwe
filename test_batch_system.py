#!/usr/bin/env python
"""
Quick Batch System Test Script
Run this inside Django shell to test all batch system components
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mill.models import City, Factory, Device, Batch, ProductionData, RawData
from mill.services.batch_production_service import BatchProductionService
from mill.services.batch_notification_service import BatchNotificationService
from django.contrib.auth.models import User, Group
from django.utils import timezone

class BatchSystemTester:
    def __init__(self):
        self.service = BatchProductionService()
        self.notification_service = BatchNotificationService()
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append((test_name, success, message))
        
    def test_conversion_factor(self):
        """Test conversion factor is set correctly"""
        try:
            expected_factor = 50.0
            actual_factor = self.service.CONVERSION_FACTOR
            success = actual_factor == expected_factor
            message = f"Expected {expected_factor}, got {actual_factor}"
            self.log_test("Conversion Factor", success, message)
        except Exception as e:
            self.log_test("Conversion Factor", False, str(e))
            
    def create_test_data(self):
        """Create test data for testing"""
        try:
            # Create test city
            self.city = City.objects.get_or_create(
                name="Test City Docker",
                defaults={'status': True}
            )[0]
            
            # Create test factory
            self.factory = Factory.objects.get_or_create(
                name="Test Factory Docker",
                defaults={
                    'city': self.city,
                    'status': True,
                    'group': 'government'
                }
            )[0]
            
            # Create test device
            self.device = Device.objects.get_or_create(
                id="DOCKER_TEST_001",
                defaults={
                    'name': "Docker Test Device",
                    'factory': self.factory,
                    'status': True,
                    'selected_counter': 'counter_1'
                }
            )[0]
            
            # Create test batch
            self.batch = Batch.objects.get_or_create(
                batch_number="DOCKER_TEST_BATCH",
                defaults={
                    'factory': self.factory,
                    'wheat_amount': Decimal('100.0'),
                    'waste_factor': Decimal('20.0'),
                    'expected_flour_output': Decimal('80.0'),
                    'status': 'in_process'
                }
            )[0]
            
            self.log_test("Test Data Creation", True, "All test objects created")
            
        except Exception as e:
            self.log_test("Test Data Creation", False, str(e))
            
    def test_production_calculation_with_production_data(self):
        """Test production calculation using ProductionData"""
        try:
            # Create production data
            production = ProductionData.objects.get_or_create(
                device=self.device,
                defaults={
                    'daily_production': 800,  # 800 units * 50kg = 40000kg = 40 tons
                    'weekly_production': 5600,
                    'monthly_production': 24000,
                    'yearly_production': 288000
                }
            )[0]
            
            # Test calculation
            result = self.service.calculate_batch_progress(self.batch)
            
            expected_output = 40.0  # 800 * 50 / 1000
            expected_progress = 50.0  # 40 / 80 * 100
            
            success = (
                abs(result['actual_flour_output'] - expected_output) < 0.1 and
                abs(result['progress_percentage'] - expected_progress) < 0.1
            )
            
            message = f"Output: {result['actual_flour_output']:.1f}t (expected {expected_output}t), Progress: {result['progress_percentage']:.1f}% (expected {expected_progress}%)"
            self.log_test("Production Calculation", success, message)
            
        except Exception as e:
            self.log_test("Production Calculation", False, str(e))
            
    def test_production_calculation_with_raw_data(self):
        """Test production calculation using RawData"""
        try:
            # Create raw data entries
            start_time = self.batch.start_date
            current_time = start_time + timedelta(hours=24)
            
            # Start data
            RawData.objects.get_or_create(
                device=self.device,
                timestamp=start_time,
                defaults={
                    'counter_1': 1000,
                    'counter_2': 500
                }
            )
            
            # Current data
            RawData.objects.get_or_create(
                device=self.device,
                timestamp=current_time,
                defaults={
                    'counter_1': 1500,  # 500 units produced
                    'counter_2': 750
                }
            )
            
            # Test calculation
            result = self.service.calculate_batch_progress(self.batch)
            
            # Expected: 500 units difference * 50 kg/unit = 25000 kg = 25 tons
            expected_output = 25.0
            expected_progress = 31.25  # 25 / 80 * 100
            
            success = (
                abs(result['actual_flour_output'] - expected_output) < 0.1 and
                abs(result['progress_percentage'] - expected_progress) < 0.1
            )
            
            message = f"RawData - Output: {result['actual_flour_output']:.1f}t (expected {expected_output}t), Progress: {result['progress_percentage']:.1f}% (expected {expected_progress}%)"
            self.log_test("RawData Calculation", success, message)
            
        except Exception as e:
            self.log_test("RawData Calculation", False, str(e))
            
    def test_batch_update(self):
        """Test batch update functionality"""
        try:
            old_output = self.batch.actual_flour_output
            result = self.service.update_batch_progress(self.batch)
            
            success = result['success']
            self.batch.refresh_from_db()
            
            message = f"Old output: {old_output}, New output: {self.batch.actual_flour_output}"
            self.log_test("Batch Update", success, message)
            
        except Exception as e:
            self.log_test("Batch Update", False, str(e))
            
    def test_batch_auto_completion(self):
        """Test auto-completion when reaching 100%"""
        try:
            # Create high production data that should trigger completion
            high_production = ProductionData.objects.get_or_create(
                device=self.device,
                defaults={'daily_production': 2000}  # Should result in >100%
            )[0]
            high_production.daily_production = 2000
            high_production.save()
            
            # Update batch
            result = self.service.update_batch_progress(self.batch)
            self.batch.refresh_from_db()
            
            success = self.batch.status == 'completed' and self.batch.is_completed
            message = f"Status: {self.batch.status}, Completed: {self.batch.is_completed}, Progress: {self.batch.progress_percentage:.1f}%"
            self.log_test("Auto Completion", success, message)
            
        except Exception as e:
            self.log_test("Auto Completion", False, str(e))
            
    def test_batch_analytics(self):
        """Test batch analytics generation"""
        try:
            analytics = self.service.get_batch_analytics(self.batch)
            
            required_keys = ['batch_info', 'production_summary', 'device_summary', 'timeline', 'efficiency_metrics']
            success = all(key in analytics for key in required_keys)
            
            message = f"Analytics keys: {list(analytics.keys())}"
            self.log_test("Batch Analytics", success, message)
            
        except Exception as e:
            self.log_test("Batch Analytics", False, str(e))
            
    def test_notification_service(self):
        """Test notification service"""
        try:
            # Create test user
            user = User.objects.get_or_create(
                username="testuser_docker",
                defaults={'email': 'test@example.com'}
            )[0]
            
            # Add user as responsible for factory
            self.factory.responsible_users.add(user)
            
            # Test notification creation (should not fail)
            self.notification_service.notify_batch_created(self.batch)
            
            self.log_test("Notification Service", True, "Notification created without errors")
            
        except Exception as e:
            self.log_test("Notification Service", False, str(e))
            
    def test_edge_cases(self):
        """Test edge cases"""
        try:
            # Test with zero expected output
            zero_batch = Batch.objects.create(
                batch_number="ZERO_TEST",
                factory=self.factory,
                wheat_amount=Decimal('0.0'),
                waste_factor=Decimal('0.0'),
                expected_flour_output=Decimal('0.0')
            )
            
            result = self.service.calculate_batch_progress(zero_batch)
            success = result['progress_percentage'] == 0.0
            
            zero_batch.delete()  # Cleanup
            
            self.log_test("Edge Cases", success, "Zero output handled correctly")
            
        except Exception as e:
            self.log_test("Edge Cases", False, str(e))
            
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Batch System Tests...")
        print("=" * 50)
        
        self.test_conversion_factor()
        self.create_test_data()
        self.test_production_calculation_with_production_data()
        self.test_production_calculation_with_raw_data()
        self.test_batch_update()
        self.test_batch_analytics()
        self.test_notification_service()
        self.test_edge_cases()
        self.test_batch_auto_completion()  # Run this last as it changes status
        
        print("=" * 50)
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success, _ in self.test_results if success)
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for name, success, message in self.test_results:
                if not success:
                    print(f"   - {name}: {message}")
        else:
            print("\n🎉 All tests passed! Batch system is working correctly.")

def main():
    """Main function to run tests"""
    tester = BatchSystemTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()