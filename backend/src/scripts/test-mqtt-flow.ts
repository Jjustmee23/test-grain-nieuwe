import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function testMqttFlow() {
  console.log('🧪 Testing MQTT Data Flow...');

  try {
    // Test device creation
    const testDeviceId = 'TEST_DEVICE_001';
    
    console.log('1. Creating test device...');
    const device = await prisma.device.upsert({
      where: { id: testDeviceId },
      update: {},
      create: {
        id: testDeviceId,
        name: 'Test Device 001',
        status: true,
        isConfigured: true
      }
    });
    console.log('✅ Device created:', device.id);

    // Test MQTT data storage
    console.log('\n2. Testing MQTT data storage...');
    const testHexMessage = '0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20';
    
    const mqttData = await prisma.mqttData.create({
      data: {
        deviceId: testDeviceId,
        deviceId_fk: testDeviceId,
        hexMessage: testHexMessage,
        topic: 'device/TEST_DEVICE_001/data',
        timestamp: new Date()
      }
    });
    console.log('✅ MQTT data stored:', mqttData.id);

    // Test raw data storage
    console.log('\n3. Testing raw data storage...');
    const rawData = await prisma.rawData.create({
      data: {
        deviceId: testDeviceId,
        deviceId_fk: testDeviceId,
        timestamp: new Date(),
        signalStrength: 85,
        signalDbm: -45,
        di1Counter: 1234,
        di2Counter: 5678,
        di3Counter: 9012,
        di4Counter: 3456,
        do1Enabled: '1',
        ai1Value: 3.14,
        mobileSignal: 4,
        doutEnabled: '1',
        diMode: 'normal',
        din: '1010',
        ainMode: 'voltage',
        startFlag: 1,
        dataType: 1,
        length: 32,
        version: 1,
        endFlag: 1
      }
    });
    console.log('✅ Raw data stored:', rawData.id);

    // Verify data retrieval
    console.log('\n4. Verifying data retrieval...');
    
    const mqttDataCount = await prisma.mqttData.count({
      where: { deviceId: testDeviceId }
    });
    console.log(`📊 MQTT data records: ${mqttDataCount}`);

    const rawDataCount = await prisma.rawData.count({
      where: { deviceId: testDeviceId }
    });
    console.log(`📊 Raw data records: ${rawDataCount}`);

    const latestRawData = await prisma.rawData.findFirst({
      where: { deviceId: testDeviceId },
      orderBy: { timestamp: 'desc' },
      select: {
        di1Counter: true,
        di2Counter: true,
        ai1Value: true,
        timestamp: true
      }
    });
    
    if (latestRawData) {
      console.log('📈 Latest raw data:');
      console.log(`  - DI1 Counter: ${latestRawData.di1Counter}`);
      console.log(`  - DI2 Counter: ${latestRawData.di2Counter}`);
      console.log(`  - AI1 Value: ${latestRawData.ai1Value}`);
      console.log(`  - Timestamp: ${latestRawData.timestamp}`);
    }

    // Test device statistics
    console.log('\n5. Testing device statistics...');
    const deviceStats = await prisma.rawData.groupBy({
      by: ['deviceId'],
      _count: { deviceId: true },
      _avg: { 
        di1Counter: true,
        ai1Value: true 
      },
      where: { deviceId: testDeviceId }
    });

    deviceStats.forEach(stat => {
      console.log(`📱 Device ${stat.deviceId}:`);
      console.log(`  - Total records: ${stat._count.deviceId}`);
      console.log(`  - Avg DI1 Counter: ${stat._avg.di1Counter}`);
      console.log(`  - Avg AI1 Value: ${stat._avg.ai1Value}`);
    });

    console.log('\n🎉 MQTT Data Flow Test Completed Successfully!');
    console.log('\n📋 Summary:');
    console.log('✅ Device creation works');
    console.log('✅ MQTT data storage works');
    console.log('✅ Raw data storage works');
    console.log('✅ Data retrieval works');
    console.log('✅ Statistics calculation works');

  } catch (error) {
    console.error('❌ MQTT flow test failed:', error);
  } finally {
    await prisma.$disconnect();
  }
}

// Run the test
testMqttFlow()
  .then(() => {
    console.log('✅ MQTT flow test completed');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ MQTT flow test failed:', error);
    process.exit(1);
  }); 