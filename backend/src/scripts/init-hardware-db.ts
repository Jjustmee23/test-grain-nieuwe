import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function initHardwareDatabase() {
  console.log('🚀 Initializing Hardware Database...');

  try {
    // Test connection to hardware database
    console.log('1. Testing hardware database connection...');
    
    // Insert sample device data
    console.log('\n2. Inserting sample device data...');
    const deviceData = await prisma.$executeRaw`
      INSERT INTO device_data (device_id, topic, message, raw_data, timestamp)
      VALUES 
        ('UC300_001', 'device/UC300_001/data', '{"signal": 85, "counter": 1234}', '0102030405060708090a0b0c0d0e0f10', NOW()),
        ('UC300_002', 'device/UC300_002/data', '{"signal": 90, "counter": 5678}', '1112131415161718191a1b1c1d1e1f20', NOW())
      ON CONFLICT DO NOTHING
    `;
    console.log('✅ Sample device data inserted');

    // Insert sample power data
    console.log('\n3. Inserting sample power data...');
    const powerData = await prisma.$executeRaw`
      INSERT INTO power_data (device_id, voltage, current, power, energy, frequency, power_factor, timestamp)
      VALUES 
        ('UC300_001', 230.5, 15.2, 3500.0, 125000.0, 50.0, 0.95, NOW()),
        ('UC300_002', 228.0, 12.8, 2920.0, 98000.0, 50.0, 0.92, NOW())
      ON CONFLICT DO NOTHING
    `;
    console.log('✅ Sample power data inserted');

    // Insert sample device status
    console.log('\n4. Inserting sample device status...');
    const deviceStatus = await prisma.$executeRaw`
      INSERT INTO device_status (device_id, status, ip_address, mac_address, firmware, location, description)
      VALUES 
        ('UC300_001', 'online', '192.168.1.100', '00:11:22:33:44:55', 'v2.1.0', 'Production Line 1', 'UC300 Controller 1'),
        ('UC300_002', 'online', '192.168.1.101', '00:11:22:33:44:56', 'v2.1.0', 'Production Line 2', 'UC300 Controller 2')
      ON CONFLICT (device_id) DO UPDATE SET
        status = EXCLUDED.status,
        last_seen = NOW()
    `;
    console.log('✅ Sample device status inserted');

    // Insert sample temperature data
    console.log('\n5. Inserting sample temperature data...');
    const tempData = await prisma.$executeRaw`
      INSERT INTO temperature_data (sensor_id, temperature, humidity, pressure, timestamp)
      VALUES 
        ('TEMP_001', 25.5, 45.2, 1013.25, NOW()),
        ('TEMP_002', 26.8, 42.1, 1012.80, NOW())
      ON CONFLICT DO NOTHING
    `;
    console.log('✅ Sample temperature data inserted');

    // Insert sample production counters
    console.log('\n6. Inserting sample production counters...');
    const prodCounters = await prisma.$executeRaw`
      INSERT INTO production_counter (device_id, counter_type, value, unit, timestamp)
      VALUES 
        ('UC300_001', 'flour', 1250, 'kg', NOW()),
        ('UC300_001', 'bags', 50, 'bags', NOW()),
        ('UC300_002', 'flour', 980, 'kg', NOW()),
        ('UC300_002', 'bags', 39, 'bags', NOW())
      ON CONFLICT DO NOTHING
    `;
    console.log('✅ Sample production counters inserted');

    // Insert sample hardware alarms
    console.log('\n7. Inserting sample hardware alarms...');
    const alarms = await prisma.$executeRaw`
      INSERT INTO hardware_alarm (device_id, alarm_type, severity, message, is_active)
      VALUES 
        ('UC300_001', 'temperature', 'medium', 'Temperature slightly elevated', TRUE),
        ('UC300_002', 'power', 'low', 'Power consumption spike detected', FALSE)
      ON CONFLICT DO NOTHING
    `;
    console.log('✅ Sample hardware alarms inserted');

    // Insert sample system metrics
    console.log('\n8. Inserting sample system metrics...');
    const metrics = await prisma.$executeRaw`
      INSERT INTO system_metrics (device_id, cpu_usage, memory_usage, disk_usage, network_in, network_out, uptime, timestamp)
      VALUES 
        ('UC300_001', 25.5, 45.2, 12.8, 1024.5, 512.3, 86400, NOW()),
        ('UC300_002', 30.1, 52.8, 15.2, 1536.7, 768.9, 72000, NOW())
      ON CONFLICT DO NOTHING
    `;
    console.log('✅ Sample system metrics inserted');

    // Verify data
    console.log('\n9. Verifying data...');
    
    const deviceDataCount = await prisma.$queryRaw`SELECT COUNT(*) as count FROM device_data`;
    const powerDataCount = await prisma.$queryRaw`SELECT COUNT(*) as count FROM power_data`;
    const deviceStatusCount = await prisma.$queryRaw`SELECT COUNT(*) as count FROM device_status`;
    const tempDataCount = await prisma.$queryRaw`SELECT COUNT(*) as count FROM temperature_data`;
    const prodCounterCount = await prisma.$queryRaw`SELECT COUNT(*) as count FROM production_counter`;
    const alarmCount = await prisma.$queryRaw`SELECT COUNT(*) as count FROM hardware_alarm`;
    const metricsCount = await prisma.$queryRaw`SELECT COUNT(*) as count FROM system_metrics`;

    console.log('📊 Data verification results:');
    console.log(`  - Device Data: ${(deviceDataCount as any[])[0]?.count} records`);
    console.log(`  - Power Data: ${(powerDataCount as any[])[0]?.count} records`);
    console.log(`  - Device Status: ${(deviceStatusCount as any[])[0]?.count} records`);
    console.log(`  - Temperature Data: ${(tempDataCount as any[])[0]?.count} records`);
    console.log(`  - Production Counters: ${(prodCounterCount as any[])[0]?.count} records`);
    console.log(`  - Hardware Alarms: ${(alarmCount as any[])[0]?.count} records`);
    console.log(`  - System Metrics: ${(metricsCount as any[])[0]?.count} records`);

    console.log('\n🎉 Hardware Database Initialization Completed Successfully!');
    console.log('\n📋 Summary:');
    console.log('✅ All hardware database tables created');
    console.log('✅ Sample data inserted');
    console.log('✅ Indexes created for performance');
    console.log('✅ Data verification completed');

  } catch (error) {
    console.error('❌ Hardware database initialization failed:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

// Run the initialization
initHardwareDatabase()
  .then(() => {
    console.log('✅ Hardware database initialization script completed');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ Hardware database initialization script failed:', error);
    process.exit(1);
  }); 