import { PrismaClient } from '@prisma/client';
import { Pool } from 'pg';

const prisma = new PrismaClient();

// Connection to hardware database
const hardwareDbPool = new Pool({
  host: 'hardware_postgres',
  port: 5432,
  database: 'hardware_db',
  user: 'hardware_user',
  password: 'hardware_password_2024',
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});

async function importAllDevices() {
  try {
    console.log('🚀 Starting device import from MQTT data...');
    
    // Get all unique device IDs from the hardware database
    const hardwareClient = await hardwareDbPool.connect();
    
    // Get all unique device IDs from uc300_official_data table
    const deviceIdsResult = await hardwareClient.query(`
      SELECT DISTINCT device_id 
      FROM uc300_official_data 
      WHERE device_id IS NOT NULL 
      ORDER BY device_id
    `);
    
    const deviceIds = deviceIdsResult.rows.map(row => row.device_id);
    console.log(`📱 Found ${deviceIds.length} unique devices in MQTT data`);
    
    // Get existing devices in mill_db
    const existingDevices = await prisma.device.findMany({
      select: { id: true }
    });
    
    const existingDeviceIds = new Set(existingDevices.map(device => device.id));
    console.log(`📱 Found ${existingDeviceIds.size} existing devices in mill_db`);
    
    // Import new devices
    let importedCount = 0;
    let updatedCount = 0;
    
    for (const deviceId of deviceIds) {
      try {
        // Get latest data for this device
        const latestDataResult = await hardwareClient.query(`
          SELECT 
            device_id,
            serial_number,
            timestamp,
            signal_strength,
            di1_counter,
            di2_counter,
            di3_counter,
            di4_counter
          FROM uc300_official_data 
          WHERE device_id = $1 
          ORDER BY timestamp DESC 
          LIMIT 1
        `, [deviceId]);
        
        if (latestDataResult.rows.length === 0) {
          continue;
        }
        
        const deviceData = latestDataResult.rows[0];
        
        if (existingDeviceIds.has(deviceId)) {
          // Update existing device status
          await prisma.device.update({
            where: { id: deviceId },
            data: { 
              status: true
            }
          });
          updatedCount++;
        } else {
          // Insert new device
          await prisma.device.create({
            data: {
              id: deviceId,
              serialNumber: deviceData.serial_number || deviceId,
              status: true, // Online
              isConfigured: false, // Not configured yet
              selectedCounter: 'counter_1' // Default counter
            }
          });
          importedCount++;
          console.log(`✅ Imported new device: ${deviceId}`);
        }
        
      } catch (error) {
        console.error(`❌ Failed to import device ${deviceId}:`, error);
      }
    }
    
    hardwareClient.release();
    
    console.log(`🎉 Device import completed!`);
    console.log(`📱 Imported: ${importedCount} new devices`);
    console.log(`📱 Updated: ${updatedCount} existing devices`);
    console.log(`📱 Total devices in mill_db: ${existingDeviceIds.size + importedCount}`);
    
  } catch (error) {
    console.error('❌ Failed to import devices:', error);
  } finally {
    await hardwareDbPool.end();
    await prisma.$disconnect();
  }
}

// Run the import
importAllDevices().catch((error) => {
  console.error('Application failed:', error);
  process.exit(1);
}); 