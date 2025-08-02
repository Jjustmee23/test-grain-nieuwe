import { PrismaClient } from '@prisma/client';
import { Pool } from 'pg';

const prisma = new PrismaClient();

// Connection to hardware database
const hardwareDbPool = new Pool({
  host: 'postgres',
  port: 5432,
  database: 'hardware_db',
  user: 'hardware_user',
  password: 'hardware_password_2024',
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});

async function importNewDevices() {
  try {
    console.log(`🔄 [${new Date().toISOString()}] Starting automatic device import...`);
    
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
    
    // Get existing devices in mill_db
    const existingDevices = await prisma.device.findMany({
      select: { id: true }
    });
    
    const existingDeviceIds = new Set(existingDevices.map(device => device.id));
    
    // Import new devices
    let importedCount = 0;
    
    for (const deviceId of deviceIds) {
      try {
        if (!existingDeviceIds.has(deviceId)) {
          // Get latest data for this device
          const latestDataResult = await hardwareClient.query(`
            SELECT 
              device_id,
              serial_number,
              timestamp,
              signal_strength
            FROM uc300_official_data 
            WHERE device_id = $1 
            ORDER BY timestamp DESC 
            LIMIT 1
          `, [deviceId]);
          
          if (latestDataResult.rows.length > 0) {
            const deviceData = latestDataResult.rows[0];
            
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
            console.log(`✅ Auto-imported new device: ${deviceId}`);
          }
        }
        
      } catch (error) {
        console.error(`❌ Failed to auto-import device ${deviceId}:`, error);
      }
    }
    
    hardwareClient.release();
    
    if (importedCount > 0) {
      console.log(`🎉 Auto-import completed: ${importedCount} new devices imported`);
    } else {
      console.log(`ℹ️ No new devices to import`);
    }
    
  } catch (error) {
    console.error('❌ Failed to auto-import devices:', error);
  }
}

// Run import every hour
const INTERVAL_HOURS = 1;
const INTERVAL_MS = INTERVAL_HOURS * 60 * 60 * 1000;

console.log(`🚀 Starting automatic device import service (every ${INTERVAL_HOURS} hour(s))`);

// Run immediately on startup
importNewDevices();

// Then run every hour
setInterval(importNewDevices, INTERVAL_MS);

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('🛑 Shutting down auto-import service...');
  await hardwareDbPool.end();
  await prisma.$disconnect();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('🛑 Shutting down auto-import service...');
  await hardwareDbPool.end();
  await prisma.$disconnect();
  process.exit(0);
}); 