import mqtt from 'mqtt';
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
  defaultMeta: { service: 'mqtt-client' },
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Database connection
const pool = new Pool({
  host: process.env.DB_HOST || 'postgres',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'mill_management',
  user: process.env.DB_USER || 'mill_user',
  password: process.env.DB_PASSWORD || 'mill_password_2024',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// MQTT Client configuration
const mqttConfig = {
  host: process.env.MQTT_BROKER || '45.154.238.114',
  port: parseInt(process.env.MQTT_PORT || '1883'),
  username: process.env.MQTT_USERNAME || 'uc300',
  password: process.env.MQTT_PASSWORD || 'grain300',
  clientId: `mill-mqtt-client-${Math.random().toString(16).slice(3)}`,
  clean: true,
  reconnectPeriod: 1000,
  connectTimeout: 30000,
};

// Initialize database tables
async function initializeDatabase() {
  try {
    const client = await pool.connect();
    
    // Create device_power_status table
    await client.query(`
      CREATE TABLE IF NOT EXISTS device_power_status (
        id SERIAL PRIMARY KEY,
        device_id VARCHAR(255) NOT NULL,
        has_power BOOLEAN DEFAULT false,
        ain1_value DECIMAL(10,2),
        last_power_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create door_status table
    await client.query(`
      CREATE TABLE IF NOT EXISTS door_status (
        id SERIAL PRIMARY KEY,
        device_id VARCHAR(255) NOT NULL,
        is_open BOOLEAN DEFAULT false,
        last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create production_data table
    await client.query(`
      CREATE TABLE IF NOT EXISTS production_data (
        id SERIAL PRIMARY KEY,
        device_id VARCHAR(255) NOT NULL,
        daily_production INTEGER DEFAULT 0,
        date DATE DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create indexes
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_device_power_status_device_id ON device_power_status(device_id);
      CREATE INDEX IF NOT EXISTS idx_door_status_device_id ON door_status(device_id);
      CREATE INDEX IF NOT EXISTS idx_production_data_device_id ON production_data(device_id);
    `);

    client.release();
    logger.info('Database tables initialized successfully');
  } catch (error) {
    logger.error('Failed to initialize database:', error);
    throw error;
  }
}

// Decode MQTT payload
function decodePayload(topic: string, payload: Buffer): any {
  try {
    const payloadStr = payload.toString();
    logger.info(`Received message on topic: ${topic}, payload: ${payloadStr}`);
    
    // Try to parse as JSON first
    try {
      return JSON.parse(payloadStr);
    } catch {
      // If not JSON, try to decode as custom format
      return decodeCustomPayload(payloadStr);
    }
  } catch (error) {
    logger.error('Failed to decode payload:', error);
    return null;
  }
}

// Decode custom payload format
function decodeCustomPayload(payload: string): any {
  // Example custom decoding - adjust based on your actual payload format
  const parts = payload.split(',');
  
  if (parts.length >= 3) {
    return {
      deviceId: parts[0],
      hasPower: parts[1] === '1',
      temperature: parseFloat(parts[2]) || null,
      timestamp: new Date()
    };
  }
  
  return {
    rawPayload: payload,
    timestamp: new Date()
  };
}

// Store device power status
async function storePowerStatus(deviceId: string, data: any) {
  try {
    const client = await pool.connect();
    
    await client.query(`
      INSERT INTO device_power_status (device_id, has_power, ain1_value, last_power_check)
      VALUES ($1, $2, $3, $4)
    `, [
      deviceId,
      data.hasPower || false,
      data.temperature || null,
      new Date()
    ]);
    
    client.release();
    logger.info(`Stored power status for device: ${deviceId}`);
  } catch (error) {
    logger.error(`Failed to store power status for device ${deviceId}:`, error);
  }
}

// Store door status
async function storeDoorStatus(deviceId: string, data: any) {
  try {
    const client = await pool.connect();
    
    await client.query(`
      INSERT INTO door_status (device_id, is_open, last_check)
      VALUES ($1, $2, $3)
    `, [
      deviceId,
      data.isOpen || false,
      new Date()
    ]);
    
    client.release();
    logger.info(`Stored door status for device: ${deviceId}`);
  } catch (error) {
    logger.error(`Failed to store door status for device ${deviceId}:`, error);
  }
}

// Store production data
async function storeProductionData(deviceId: string, data: any) {
  try {
    const client = await pool.connect();
    
    await client.query(`
      INSERT INTO production_data (device_id, daily_production, date)
      VALUES ($1, $2, $3)
      ON CONFLICT (device_id, date) 
      DO UPDATE SET daily_production = EXCLUDED.daily_production
    `, [
      deviceId,
      data.dailyProduction || 0,
      new Date()
    ]);
    
    client.release();
    logger.info(`Stored production data for device: ${deviceId}`);
  } catch (error) {
    logger.error(`Failed to store production data for device ${deviceId}:`, error);
  }
}

// Handle MQTT messages
function handleMessage(topic: string, payload: Buffer) {
  try {
    const decodedData = decodePayload(topic, payload);
    if (!decodedData) return;

    // Extract device ID from topic or data
    const deviceId = extractDeviceId(topic, decodedData);
    if (!deviceId) {
      logger.warn('No device ID found in message');
      return;
    }

    // Route message based on topic
    if (topic.includes('power') || topic.includes('status')) {
      storePowerStatus(deviceId, decodedData);
    } else if (topic.includes('door')) {
      storeDoorStatus(deviceId, decodedData);
    } else if (topic.includes('production') || topic.includes('count')) {
      storeProductionData(deviceId, decodedData);
    } else {
      // Default to power status
      storePowerStatus(deviceId, decodedData);
    }
  } catch (error) {
    logger.error('Failed to handle message:', error);
  }
}

// Extract device ID from topic or data
function extractDeviceId(topic: string, data: any): string | null {
  // Try to extract from topic first
  const topicParts = topic.split('/');
  if (topicParts.length > 1) {
    return topicParts[1];
  }
  
  // Try to extract from data
  if (data.deviceId) {
    return data.deviceId;
  }
  
  // Try to extract from topic using regex
  const deviceMatch = topic.match(/device[\/\-]?(\w+)/i);
  if (deviceMatch) {
    return deviceMatch[1];
  }
  
  return null;
}

// Main function
async function main() {
  try {
    // Initialize database
    await initializeDatabase();
    
    // Connect to MQTT broker
    logger.info('Connecting to MQTT broker...');
    const client = mqtt.connect(mqttConfig);
    
    client.on('connect', () => {
      logger.info('Connected to MQTT broker');
      
      // Subscribe to all relevant topics
      const topics = [
        'device/+/power',
        'device/+/status',
        'device/+/door',
        'device/+/production',
        'device/+/count',
        'uc300/+/+',  // For uc300 username topics
        'grain/+/+',  // For grain-related topics
        'mill/+/+'    // For mill-related topics
      ];
      
      topics.forEach(topic => {
        client.subscribe(topic, (err) => {
          if (err) {
            logger.error(`Failed to subscribe to ${topic}:`, err);
          } else {
            logger.info(`Subscribed to ${topic}`);
          }
        });
      });
    });
    
    client.on('message', (topic, payload) => {
      handleMessage(topic, payload);
    });
    
    client.on('error', (error) => {
      logger.error('MQTT client error:', error);
    });
    
    client.on('close', () => {
      logger.info('MQTT connection closed');
    });
    
    client.on('reconnect', () => {
      logger.info('MQTT reconnecting...');
    });
    
    // Graceful shutdown
    process.on('SIGINT', async () => {
      logger.info('Shutting down MQTT client...');
      client.end();
      await pool.end();
      process.exit(0);
    });
    
    process.on('SIGTERM', async () => {
      logger.info('Shutting down MQTT client...');
      client.end();
      await pool.end();
      process.exit(0);
    });
    
  } catch (error) {
    logger.error('Failed to start MQTT client:', error);
    process.exit(1);
  }
}

// Start the application
main().catch((error) => {
  logger.error('Application failed to start:', error);
  process.exit(1);
}); 