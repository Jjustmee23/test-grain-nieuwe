from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from mill.models import Batch, Factory, Device, RawData, ProductionData, City
from mill.services.batch_production_service import BatchProductionService
from datetime import timedelta


class BatchProductionServiceTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.service = BatchProductionService()
        
        # Create test city
        self.city = City.objects.create(name="Test City", status=True)
        
        # Create test factory
        self.factory = Factory.objects.create(
            name="Test Factory",
            city=self.city,
            status=True
        )
        
        # Create test device
        self.device = Device.objects.create(
            id="test_device_001",
            name="Test Device",
            factory=self.factory,
            status=True,
            selected_counter="counter_1"
        )
        
        # Create test batch
        self.batch = Batch.objects.create(
            batch_number="TEST_001",
            factory=self.factory,
            wheat_amount=Decimal('100.0'),
            waste_factor=Decimal('20.0'),
            expected_flour_output=Decimal('80.0'),
            status='in_process'
        )
    
    def test_conversion_factor(self):
        """Test that conversion factor is correctly set"""
        self.assertEqual(self.service.CONVERSION_FACTOR, 50.0)
        self.assertEqual(self.service.TONS_PER_KG, 1000.0)
    
    def test_calculate_batch_progress_no_factory(self):
        """Test batch progress calculation when no factory is assigned"""
        batch_no_factory = Batch.objects.create(
            batch_number="TEST_NO_FACTORY",
            wheat_amount=Decimal('100.0'),
            waste_factor=Decimal('20.0')
        )
        
        result = self.service.calculate_batch_progress(batch_no_factory)
        
        self.assertEqual(result['current_value'], 0)
        self.assertEqual(result['actual_flour_output'], 0.0)
        self.assertEqual(result['progress_percentage'], 0.0)
        self.assertEqual(result['data_source'], 'no_factory')
    
    def test_calculate_batch_progress_no_devices(self):
        """Test batch progress calculation when factory has no devices"""
        factory_no_devices = Factory.objects.create(
            name="Empty Factory",
            city=self.city,
            status=True
        )
        
        batch_no_devices = Batch.objects.create(
            batch_number="TEST_NO_DEVICES",
            factory=factory_no_devices,
            wheat_amount=Decimal('100.0'),
            waste_factor=Decimal('20.0')
        )
        
        result = self.service.calculate_batch_progress(batch_no_devices)
        
        self.assertEqual(result['current_value'], 0)
        self.assertEqual(result['actual_flour_output'], 0.0)
        self.assertEqual(result['progress_percentage'], 0.0)
        self.assertEqual(result['data_source'], 'no_devices')
    
    def test_calculate_batch_progress_with_raw_data(self):
        """Test batch progress calculation with RawData"""
        # Create RawData entries
        start_time = self.batch.start_date
        current_time = start_time + timedelta(hours=24)
        
        # Start data
        RawData.objects.create(
            device=self.device,
            timestamp=start_time,
            counter_1=1000,
            counter_2=500
        )
        
        # Current data
        RawData.objects.create(
            device=self.device,
            timestamp=current_time,
            counter_1=1500,  # 500 units produced
            counter_2=750
        )
        
        result = self.service.calculate_batch_progress(self.batch)
        
        # Expected: 500 units * 50 kg/unit = 25000 kg = 25 tons
        self.assertEqual(result['current_value'], 1500)
        self.assertAlmostEqual(result['actual_flour_output'], 25.0, places=2)
        
        # Progress: 25 tons / 80 tons = 31.25%
        self.assertAlmostEqual(result['progress_percentage'], 31.25, places=2)
        
        self.assertIn('raw_data', result['data_source'])
    
    def test_calculate_batch_progress_with_production_data(self):
        """Test batch progress calculation with ProductionData as fallback"""
        # Create ProductionData
        ProductionData.objects.create(
            device=self.device,
            daily_production=800
        )
        
        result = self.service.calculate_batch_progress(self.batch)
        
        # Expected: 800 units * 50 kg/unit = 40000 kg = 40 tons
        self.assertEqual(result['current_value'], 800)
        self.assertAlmostEqual(result['actual_flour_output'], 40.0, places=2)
        
        # Progress: 40 tons / 80 tons = 50%
        self.assertAlmostEqual(result['progress_percentage'], 50.0, places=2)
        
        self.assertIn('production_data', result['data_source'])
    
    def test_update_batch_progress_dry_run(self):
        """Test batch progress update in dry run mode"""
        # Create some production data
        ProductionData.objects.create(
            device=self.device,
            daily_production=400
        )
        
        result = self.service.update_batch_progress(self.batch, dry_run=True)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['dry_run'])
        self.assertIn('data', result)
        
        # Batch should not be updated in dry run
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.current_value, 0)  # Should remain unchanged
    
    def test_update_batch_progress_auto_complete(self):
        """Test that batch is auto-completed when reaching 100%"""
        # Create production data that exceeds expected output
        ProductionData.objects.create(
            device=self.device,
            daily_production=2000  # This should result in >100% progress
        )
        
        result = self.service.update_batch_progress(self.batch)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['batch_updated'])
        
        # Batch should be auto-completed
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, 'completed')
        self.assertTrue(self.batch.is_completed)
        self.assertIsNotNone(self.batch.end_date)
    
    def test_get_batch_analytics(self):
        """Test batch analytics generation"""
        # Create some test data
        ProductionData.objects.create(
            device=self.device,
            daily_production=600
        )
        
        analytics = self.service.get_batch_analytics(self.batch)
        
        self.assertIsNotNone(analytics)
        self.assertIn('batch_info', analytics)
        self.assertIn('production_summary', analytics)
        self.assertIn('device_summary', analytics)
        self.assertIn('timeline', analytics)
        self.assertIn('efficiency_metrics', analytics)
        
        # Check batch info
        batch_info = analytics['batch_info']
        self.assertEqual(batch_info['batch_number'], self.batch.batch_number)
        self.assertEqual(batch_info['factory'], self.factory.name)
        
        # Check device summary
        device_summary = analytics['device_summary']
        self.assertEqual(device_summary['total_devices'], 1)
        self.assertEqual(device_summary['active_devices'], 1)
        self.assertEqual(len(device_summary['device_details']), 1)
    
    def test_efficiency_metrics_calculation(self):
        """Test efficiency metrics calculation"""
        analytics = self.service.get_batch_analytics(self.batch)
        efficiency = analytics['efficiency_metrics']
        
        self.assertIn('duration_days', efficiency)
        self.assertIn('expected_duration_days', efficiency)
        self.assertIn('time_efficiency', efficiency)
        self.assertIn('production_efficiency', efficiency)
        self.assertIn('overall_efficiency', efficiency)
        
        # Check that values are reasonable
        self.assertGreaterEqual(efficiency['time_efficiency'], 0)
        self.assertLessEqual(efficiency['time_efficiency'], 100)
        self.assertGreaterEqual(efficiency['overall_efficiency'], 0)
    
    def test_multiple_devices_calculation(self):
        """Test batch progress calculation with multiple devices"""
        # Create second device
        device2 = Device.objects.create(
            id="test_device_002",
            name="Test Device 2",
            factory=self.factory,
            status=True,
            selected_counter="counter_1"
        )
        
        # Create production data for both devices
        ProductionData.objects.create(
            device=self.device,
            daily_production=300
        )
        
        ProductionData.objects.create(
            device=device2,
            daily_production=200
        )
        
        result = self.service.calculate_batch_progress(self.batch)
        
        # Total: 500 units, should be combined from both devices
        self.assertEqual(result['current_value'], 500)
        self.assertEqual(result['device_count'], 2)
        
        # Expected: 500 units * 50 kg/unit = 25000 kg = 25 tons
        self.assertAlmostEqual(result['actual_flour_output'], 25.0, places=2)
    
    def test_edge_case_zero_expected_output(self):
        """Test handling of edge case with zero expected output"""
        batch_zero = Batch.objects.create(
            batch_number="TEST_ZERO",
            factory=self.factory,
            wheat_amount=Decimal('0.0'),
            waste_factor=Decimal('0.0'),
            expected_flour_output=Decimal('0.0')
        )
        
        result = self.service.calculate_batch_progress(batch_zero)
        
        # Should handle division by zero gracefully
        self.assertEqual(result['progress_percentage'], 0.0)
    
    def test_negative_production_values(self):
        """Test handling of negative production values"""
        # Create RawData with decreasing counter values (shouldn't happen normally)
        start_time = self.batch.start_date
        current_time = start_time + timedelta(hours=24)
        
        RawData.objects.create(
            device=self.device,
            timestamp=start_time,
            counter_1=1000
        )
        
        RawData.objects.create(
            device=self.device,
            timestamp=current_time,
            counter_1=800  # Decreased value
        )
        
        result = self.service.calculate_batch_progress(self.batch)
        
        # Should handle negative differences gracefully
        self.assertGreaterEqual(result['actual_flour_output'], 0)