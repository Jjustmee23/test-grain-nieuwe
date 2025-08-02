import mqtt from 'mqtt';
import { Pool } from 'pg';
import winston from 'winston';
import dotenv from 'dotenv';
import { OfficialUC300Decoder } from './official-uc300-decoder';
import { UC300CommandSender } from './uc300-command-sender';

// Load environment variables
dotenv.config();

// Configure logger with high throughput settings
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'uc300-official-client' },
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// High-performance database connection pool
const pool = new Pool({
  host: process.env.DB_HOST || 'postgres',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'mill_management',
  user: process.env.DB_USER || 'mill_user',
  password: process.env.DB_PASSWORD || 'mill_password_2024',
  max: 50, // Increased for high throughput
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
  // High throughput settings
  statement_timeout: 30000,
  query_timeout: 30000
});

// Connection pool for mill_db (application database)
const millDbPool = new Pool({
  host: process.env.DB_HOST || 'postgres',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: 'mill_db',
  user: process.env.DB_USER || 'mill_user',
  password: process.env.DB_PASSWORD || 'mill_password_2024',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});

// Track discovered devices to avoid duplicate registrations
const discoveredDevices = new Set<string>();

// Function to register new device in mill_db
async function registerNewDevice(deviceId: string, serialNumber?: string) {
  try {
    // Skip if already discovered in this session
    if (discoveredDevices.has(deviceId)) {
      return;
    }
    
    const client = await millDbPool.connect();
    
    // Check if device already exists in mill_db
    const existingDevice = await client.query(
      'SELECT id FROM device WHERE id = $1',
      [deviceId]
    );
    
    if (existingDevice.rows.length === 0) {
      // Register new device
      await client.query(`
        INSERT INTO device (id, serial_number, status, is_configured, selected_counter, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
      `, [
        deviceId,
        serialNumber || deviceId,
        true, // Online
        false, // Not configured yet
        'counter_1' // Default counter
      ]);
      
      logger.info(`📱 Registered new device: ${deviceId}`);
    } else {
      // Update existing device status to online
      await client.query(
        'UPDATE device SET status = $1, updated_at = NOW() WHERE id = $2',
        [true, deviceId]
      );
    }
    
    client.release();
    discoveredDevices.add(deviceId);
    
  } catch (error) {
    logger.error(`❌ Failed to register device ${deviceId}:`, error);
  }
}

// MQTT Client configuration for high throughput
const mqttConfig = {
  host: process.env.MQTT_BROKER || '45.154.238.114',
  port: parseInt(process.env.MQTT_PORT || '1883'),
  username: process.env.MQTT_USERNAME || 'uc300',
  password: process.env.MQTT_PASSWORD || 'grain300',
  clientId: `uc300-official-${Math.random().toString(16).slice(3)}`,
  clean: true,
  reconnectPeriod: 1000,
  connectTimeout: 30000,
  // High throughput settings
  keepalive: 60,
  reschedulePings: true,
  queueQoSZero: false
};

// Performance tracking
let messageCount = 0;
let startTime = Date.now();

// Initialize database tables for high throughput
async function initializeDatabase() {
  try {
    const client = await pool.connect();
    
    // Create optimized uc300_official_data table
    await client.query(`
      CREATE TABLE IF NOT EXISTS uc300_official_data (
        id SERIAL PRIMARY KEY,
        device_id VARCHAR(30) NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        topic VARCHAR(255),
        data_type VARCHAR(10),
        packet_length INTEGER,
        
        -- Device info (from F3)
        serial_number VARCHAR(20),
        hardware_version VARCHAR(10),
        firmware_version VARCHAR(10),
        imei VARCHAR(20),
        imsi VARCHAR(20),
        iccid VARCHAR(25),
        
        -- Signal and status
        signal_strength INTEGER,
        signal_dbm INTEGER,
        
        -- Digital Inputs
        di1_mode VARCHAR(20),
        di1_status VARCHAR(10),
        di1_counter INTEGER,
        di2_mode VARCHAR(20),
        di2_status VARCHAR(10),
        di2_counter INTEGER,
        di3_mode VARCHAR(20),
        di3_status VARCHAR(10),
        di3_counter INTEGER,
        di4_mode VARCHAR(20),
        di4_status VARCHAR(10),
        di4_counter INTEGER,
        
        -- Digital Outputs
        do1_enabled BOOLEAN,
        do1_status VARCHAR(10),
        do2_enabled BOOLEAN,
        do2_status VARCHAR(10),
        
        -- Analog Inputs
        ai1_mode VARCHAR(20),
        ai1_value DECIMAL(10,3),
        ai2_mode VARCHAR(20),
        ai2_value DECIMAL(10,3),
        ai3_mode VARCHAR(20),
        ai3_value DECIMAL(10,3),
        ai4_mode VARCHAR(20),
        ai4_value DECIMAL(10,3),
        ai5_mode VARCHAR(20),
        ai5_value DECIMAL(10,3),
        ai6_mode VARCHAR(20),
        ai6_value DECIMAL(10,3),
        ai7_mode VARCHAR(20),
        ai7_value DECIMAL(10,3),
        ai8_mode VARCHAR(20),
        ai8_value DECIMAL(10,3),
        
        -- Modbus data
        modbus_data JSONB,
        
        -- Raw data
        raw_hex TEXT,
        decoded_data JSONB,
        
        -- Performance fields
        processing_time_ms INTEGER,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create optimized indexes for high throughput
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_uc300_official_device_id ON uc300_official_data(device_id);
      CREATE INDEX IF NOT EXISTS idx_uc300_official_timestamp ON uc300_official_data(timestamp);
      CREATE INDEX IF NOT EXISTS idx_uc300_official_data_type ON uc300_official_data(data_type);
      CREATE INDEX IF NOT EXISTS idx_uc300_official_created_at ON uc300_official_data(created_at);
    `);

    client.release();
    logger.info('✅ Database tables initialized for official UC300 decoder');
  } catch (error) {
    logger.error('❌ Failed to initialize database:', error);
    throw error;
  }
}

// High-performance data storage with batch processing
const batchQueue: any[] = [];
const BATCH_SIZE = 100;
const BATCH_TIMEOUT = 5000; // 5 seconds

async function storeUC300OfficialData(deviceId: string, topic: string, payload: any, processingTime: number) {
  try {
    const data = {
      device_id: deviceId,
      topic,
      data_type: `0x${payload.dataType.toString(16).toUpperCase()}`,
      packet_length: payload.packetLength,
      
      // Device info
      serial_number: payload.data?.serialNumber || null,
      hardware_version: payload.data?.hardwareVersion || null,
      firmware_version: payload.data?.firmwareVersion || null,
      imei: payload.data?.imei || null,
      imsi: payload.data?.imsi || null,
      iccid: payload.data?.iccid || null,
      
      // Signal
      signal_strength: payload.data?.signalStrength || null,
      signal_dbm: payload.data?.signalStrength ? (-113 + 2 * payload.data.signalStrength) : null,
      
      // Digital Inputs
      di1_mode: payload.data?.diModes?.[0] !== undefined ? getDIModeName(payload.data.diModes[0]) : null,
      di1_status: payload.data?.diStatus?.[0] !== undefined ? (payload.data.diStatus[0] ? 'High' : 'Low') : null,
      di1_counter: payload.data?.counterValues?.[0] || null,
      di2_mode: payload.data?.diModes?.[1] !== undefined ? getDIModeName(payload.data.diModes[1]) : null,
      di2_status: payload.data?.diStatus?.[1] !== undefined ? (payload.data.diStatus[1] ? 'High' : 'Low') : null,
      di2_counter: payload.data?.counterValues?.[1] || null,
      di3_mode: payload.data?.diModes?.[2] !== undefined ? getDIModeName(payload.data.diModes[2]) : null,
      di3_status: payload.data?.diStatus?.[2] !== undefined ? (payload.data.diStatus[2] ? 'High' : 'Low') : null,
      di3_counter: payload.data?.counterValues?.[2] || null,
      di4_mode: payload.data?.diModes?.[3] !== undefined ? getDIModeName(payload.data.diModes[3]) : null,
      di4_status: payload.data?.diStatus?.[3] !== undefined ? (payload.data.diStatus[3] ? 'High' : 'Low') : null,
      di4_counter: payload.data?.counterValues?.[3] || null,
      
      // Digital Outputs
      do1_enabled: payload.data?.doutEnabled?.[0] || false,
      do1_status: payload.data?.doutStatus?.[0] !== undefined ? (payload.data.doutStatus[0] ? 'Open' : 'Closed') : null,
      do2_enabled: payload.data?.doutEnabled?.[1] || false,
      do2_status: payload.data?.doutStatus?.[1] !== undefined ? (payload.data.doutStatus[1] ? 'Open' : 'Closed') : null,
      
      // Analog Inputs
      ai1_mode: payload.data?.ainModes?.[0] !== undefined ? getAIModeName(payload.data.ainModes[0]) : null,
      ai1_value: payload.data?.ainValues?.[0] || null,
      ai2_mode: payload.data?.ainModes?.[1] !== undefined ? getAIModeName(payload.data.ainModes[1]) : null,
      ai2_value: payload.data?.ainValues?.[1] || null,
      ai3_mode: payload.data?.ainModes?.[2] !== undefined ? getAIModeName(payload.data.ainModes[2]) : null,
      ai3_value: payload.data?.ainValues?.[2] || null,
      ai4_mode: payload.data?.ainModes?.[3] !== undefined ? getAIModeName(payload.data.ainModes[3]) : null,
      ai4_value: payload.data?.ainValues?.[3] || null,
      ai5_mode: payload.data?.ainModes?.[4] !== undefined ? getAIModeName(payload.data.ainModes[4]) : null,
      ai5_value: payload.data?.ainValues?.[4] || null,
      ai6_mode: payload.data?.ainModes?.[5] !== undefined ? getAIModeName(payload.data.ainModes[5]) : null,
      ai6_value: payload.data?.ainValues?.[5] || null,
      ai7_mode: payload.data?.ainModes?.[6] !== undefined ? getAIModeName(payload.data.ainModes[6]) : null,
      ai7_value: payload.data?.ainValues?.[6] || null,
      ai8_mode: payload.data?.ainModes?.[7] !== undefined ? getAIModeName(payload.data.ainModes[7]) : null,
      ai8_value: payload.data?.ainValues?.[7] || null,
      
      // Modbus data
      modbus_data: payload.data?.modbusData ? JSON.stringify(payload.data.modbusData) : null,
      
      // Raw data
      raw_hex: payload.rawHex,
      decoded_data: JSON.stringify(OfficialUC300Decoder.getReadableStatus(payload)),
      
      // Performance
      processing_time_ms: processingTime
    };
    
    batchQueue.push(data);
    
    // Process batch if full or timeout reached
    if (batchQueue.length >= BATCH_SIZE) {
      await processBatch();
    }
    
  } catch (error) {
    logger.error(`❌ Failed to queue UC300 official data for device ${deviceId}:`, error);
  }
}

async function processBatch() {
  if (batchQueue.length === 0) return;
  
  try {
    const client = await pool.connect();
    const batch = batchQueue.splice(0, BATCH_SIZE);
    
    // Use COPY for high-performance bulk insert
    const query = `
      INSERT INTO uc300_official_data (
        device_id, topic, data_type, packet_length, serial_number, hardware_version, firmware_version,
        imei, imsi, iccid, signal_strength, signal_dbm, di1_mode, di1_status, di1_counter,
        di2_mode, di2_status, di2_counter, di3_mode, di3_status, di3_counter, di4_mode, di4_status, di4_counter,
        do1_enabled, do1_status, do2_enabled, do2_status, ai1_mode, ai1_value, ai2_mode, ai2_value,
        ai3_mode, ai3_value, ai4_mode, ai4_value, ai5_mode, ai5_value, ai6_mode, ai6_value,
        ai7_mode, ai7_value, ai8_mode, ai8_value, modbus_data, raw_hex, decoded_data, processing_time_ms
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36, $37, $38,
                $39, $40, $41, $42, $43, $44, $45, $46, $47, $48)
    `;
    
    await client.query('BEGIN');
    
    for (const data of batch) {
      await client.query(query, [
        data.device_id, data.topic, data.data_type, data.packet_length, data.serial_number,
        data.hardware_version, data.firmware_version, data.imei, data.imsi, data.iccid,
        data.signal_strength, data.signal_dbm, data.di1_mode, data.di1_status, data.di1_counter,
        data.di2_mode, data.di2_status, data.di2_counter, data.di3_mode, data.di3_status, data.di3_counter,
        data.di4_mode, data.di4_status, data.di4_counter, data.do1_enabled, data.do1_status,
        data.do2_enabled, data.do2_status, data.ai1_mode, data.ai1_value, data.ai2_mode, data.ai2_value,
        data.ai3_mode, data.ai3_value, data.ai4_mode, data.ai4_value, data.ai5_mode, data.ai5_value,
        data.ai6_mode, data.ai6_value, data.ai7_mode, data.ai7_value, data.ai8_mode, data.ai8_value,
        data.modbus_data, data.raw_hex, data.decoded_data, data.processing_time_ms
      ]);
    }
    
    await client.query('COMMIT');
    client.release();
    
    logger.info(`✅ Processed batch of ${batch.length} messages`);
    
  } catch (error) {
    logger.error('❌ Failed to process batch:', error);
  }
}

// Helper functions
function getDIModeName(mode: number): string {
  const modeNames = ['Disabled', 'Digital Input', 'Counter-Stop', 'Counter-Start'];
  return modeNames[mode] || 'Unknown';
}

function getAIModeName(mode: number): string {
  const modeNames = ['Disabled', 'Success', 'Failed', 'Reserved'];
  return modeNames[mode] || 'Unknown';
}

// Extract device ID from topic
function extractDeviceIdFromTopic(topic: string): string | null {
  // Topic format: uc/{deviceId}/ucp/14/status
  const match = topic.match(/uc\/([^\/]+)\//);
  return match ? match[1] : null;
}

// High-performance message handler
function handleMessage(topic: string, payload: Buffer) {
  const startProcessing = Date.now();
  
  try {
    messageCount++;
    
    // Extract device ID from topic
    const deviceId = extractDeviceIdFromTopic(topic);
    if (!deviceId) {
      return;
    }
    
    // Register device immediately when detected
    registerNewDevice(deviceId);
    
    // Handle different message types
    if (topic.includes('/dev')) {
      // Device online/offline status
      const status = payload.toString();
      logger.info(`📱 Device ${deviceId}: ${status}`);
      
      // Update device status in mill_db
      updateDeviceStatus(deviceId, status === 'online');
      return;
    }
    
    // Decode payload using official decoder
    const decodedPayload = OfficialUC300Decoder.decodePayload(payload);
    
    if (decodedPayload) {
      const processingTime = Date.now() - startProcessing;
      
      // Add raw hex for storage
      (decodedPayload as any).rawHex = payload.toString('hex').toUpperCase();
      
      // Store in database
      storeUC300OfficialData(deviceId, topic, decodedPayload, processingTime);
      
      // Update device status to online
      updateDeviceStatus(deviceId, true);
      
      // Log every 100th message for monitoring
      if (messageCount % 100 === 0) {
        const readableStatus = OfficialUC300Decoder.getReadableStatus(decodedPayload);
        logger.info(`📊 Message #${messageCount} - Device: ${deviceId}`, readableStatus);
      }
    } else {
      logger.warn(`⚠️ Failed to decode payload from device ${deviceId}`);
    }
    
  } catch (error) {
    logger.error('❌ Failed to handle MQTT message:', error);
  }
}

// Function to update device status in mill_db
async function updateDeviceStatus(deviceId: string, isOnline: boolean) {
  try {
    const client = await millDbPool.connect();
    
    await client.query(
      'UPDATE device SET status = $1, updated_at = NOW() WHERE id = $2',
      [isOnline, deviceId]
    );
    
    client.release();
  } catch (error) {
    logger.error(`❌ Failed to update device status for ${deviceId}:`, error);
  }
}

// Performance monitoring
setInterval(() => {
  const elapsed = (Date.now() - startTime) / 1000;
  const rate = messageCount / elapsed;
  
  logger.info(`📈 Performance: ${messageCount} messages in ${elapsed.toFixed(1)}s (${rate.toFixed(1)} msg/s)`);
  
  // Process any remaining batch
  if (batchQueue.length > 0) {
    processBatch();
  }
}, 30000); // Every 30 seconds

// Main function
async function main() {
  try {
    // Initialize database
    await initializeDatabase();
    
    // Connect to MQTT broker
    logger.info('🔌 Connecting to UC300 Official MQTT broker...');
    logger.info(`📍 Broker: ${mqttConfig.host}:${mqttConfig.port}`);
    logger.info(`👤 Username: ${mqttConfig.username}`);
    logger.info(`📡 Expected: 300+ devices, every 5 minutes = 3600+ messages/hour`);
    
    const client = mqtt.connect(mqttConfig);
    
    client.on('connect', () => {
      logger.info('✅ Connected to UC300 Official MQTT broker!');
      
      // Subscribe to UC300 topics
      const topics = [
        'uc/+/ucp/14/status',    // UC300 status data (F2, F3, F4)
        'uc/+/ucp/14/dev',       // UC300 device status
        'uc/+/ucp/14/cmd/update/accepted', // Command responses
        'uc/+/ucp/14/cmd/update/rejected', // Command errors
        'uc/+/+/+',              // All UC300 topics
        '#'                      // All topics (for discovery)
      ];
      
      logger.info('📡 Subscribing to UC300 topics for high throughput...');
      topics.forEach(topic => {
        client.subscribe(topic, (err) => {
          if (err) {
            logger.error(`❌ Failed to subscribe to ${topic}:`, err);
          } else {
            logger.info(`✅ Subscribed to ${topic}`);
          }
        });
      });
      
      // Initialize command sender for testing
      const commandSender = new UC300CommandSender(client, '6445E28148720016');
      
      // Test authentication after 10 seconds
      setTimeout(async () => {
        logger.info('🔐 Testing UC300 command authentication...');
        const authResult = await commandSender.sendPasswordValidation();
        if (authResult) {
          logger.info('✅ Authentication successful - ready to send commands');
          
          // Test counter reset after 5 seconds
          setTimeout(async () => {
            logger.info('🔢 Testing counter reset commands...');
            const resetResults = await commandSender.resetAllCounters();
            logger.info('🔢 Counter reset results:', resetResults);
          }, 5000);
        } else {
          logger.error('❌ Authentication failed');
        }
      }, 10000);
    });
    
    client.on('message', (topic, payload) => {
      handleMessage(topic, payload);
    });
    
    client.on('error', (error) => {
      logger.error('❌ MQTT client error:', error);
    });
    
    client.on('close', () => {
      logger.info('🔌 MQTT connection closed');
    });
    
    client.on('reconnect', () => {
      logger.info('🔄 MQTT reconnecting...');
    });
    
    // Graceful shutdown
    process.on('SIGINT', async () => {
      logger.info('🛑 Shutting down UC300 Official MQTT client...');
      await processBatch(); // Process remaining batch
      client.end();
      await pool.end();
      process.exit(0);
    });
    
    process.on('SIGTERM', async () => {
      logger.info('�� Shutting down UC300 Official MQTT client...');
      await processBatch(); // Process remaining batch
      client.end();
      await pool.end();
      process.exit(0);
    });
    
  } catch (error) {
    logger.error('Failed to start UC300 Official MQTT client:', error);
    process.exit(1);
  }
}

// Start the application
main().catch((error) => {
  logger.error('Application failed to start:', error);
  process.exit(1);
}); 