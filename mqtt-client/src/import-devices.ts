import { Pool } from 'pg';
import winston from 'winston';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Configure logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'device-importer' },
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Database connection pools
const hardwareDbPool = new Pool({
  host: process.env.DB_HOST || 'postgres',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'mill_management',
  user: process.env.DB_USER || 'mill_user',
  password: process.env.DB_PASSWORD || 'mill_password_2024',
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});

const millDbPool = new Pool({
  host: process.env.DB_HOST || 'postgres',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: 'mill_db',
  user: process.env.DB_USER || 'mill_user',
  password: process.env.DB_PASSWORD || 'mill_password_2024',
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});

async function importAllDevices() {
  try {
    logger.info('🚀 Starting device import from MQTT data...');
    
    // Get all unique device IDs from the hardware database
    const hardwareClient = await hardwareDbPool.connect();
    const millClient = await millDbPool.connect();
    
    // Get all unique device IDs from uc300_official_data table
    const deviceIdsResult = await hardwareClient.query(`
      SELECT DISTINCT device_id 
      FROM uc300_official_data 
      WHERE device_id IS NOT NULL 
      ORDER BY device_id
    `);
    
    const deviceIds = deviceIdsResult.rows.map(row => row.device_id);
    logger.info(`📱 Found ${deviceIds.length} unique devices in MQTT data`);
    
    // Get existing devices in mill_db
    const existingDevicesResult = await millClient.query(`
      SELECT id FROM device
    `);
    
    const existingDeviceIds = new Set(existingDevicesResult.rows.map(row => row.id));
    logger.info(`📱 Found ${existingDeviceIds.size} existing devices in mill_db`);
    
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
          await millClient.query(`
            UPDATE device 
            SET 
              status = true,
              updated_at = NOW()
            WHERE id = $1
          `, [deviceId]);
          updatedCount++;
        } else {
          // Insert new device
          await millClient.query(`
            INSERT INTO device (
              id, 
              serial_number, 
              status, 
              is_configured, 
              selected_counter, 
              created_at, 
              updated_at
            ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
          `, [
            deviceId,
            deviceData.serial_number || deviceId,
            true, // Online
            false, // Not configured yet
            'counter_1' // Default counter
          ]);
          importedCount++;
          logger.info(`✅ Imported new device: ${deviceId}`);
        }
        
      } catch (error) {
        logger.error(`❌ Failed to import device ${deviceId}:`, error);
      }
    }
    
    hardwareClient.release();
    millClient.release();
    
    logger.info(`🎉 Device import completed!`);
    logger.info(`📱 Imported: ${importedCount} new devices`);
    logger.info(`📱 Updated: ${updatedCount} existing devices`);
    logger.info(`📱 Total devices in mill_db: ${existingDeviceIds.size + importedCount}`);
    
  } catch (error) {
    logger.error('❌ Failed to import devices:', error);
  } finally {
    await hardwareDbPool.end();
    await millDbPool.end();
  }
}

// Run the import
importAllDevices().catch((error) => {
  logger.error('Application failed:', error);
  process.exit(1);
}); 