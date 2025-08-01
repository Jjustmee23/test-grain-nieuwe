import { PrismaClient } from '@prisma/client';
import mqtt from 'mqtt';

const prisma = new PrismaClient();

class MqttService {
  private client: mqtt.Client | null = null;
  private isConnected = false;

  async start() {
    console.log('🚀 Starting MQTT service...');

    try {
      // Connect to MQTT broker
      this.client = mqtt.connect({
        host: process.env.MQTT_BROKER || '45.154.238.114',
        port: parseInt(process.env.MQTT_PORT || '1883'),
        username: process.env.MQTT_USERNAME || 'uc300',
        password: process.env.MQTT_PASSWORD || 'grain300',
        clientId: `mill-backend-${Date.now()}`,
        reconnectPeriod: 5000,
        connectTimeout: 30000
      });

      this.client.on('connect', () => {
        console.log('✅ Connected to MQTT broker');
        this.isConnected = true;
        
        // Subscribe to all device topics
        this.client?.subscribe('device/+/data', (err) => {
          if (err) {
            console.error('❌ MQTT subscription error:', err);
          } else {
            console.log('📡 Subscribed to device/+/data topics');
          }
        });
      });

      this.client.on('message', async (topic, message) => {
        try {
          await this.handleMessage(topic, message);
        } catch (error) {
          console.error('❌ Error handling MQTT message:', error);
        }
      });

      this.client.on('error', (error) => {
        console.error('❌ MQTT error:', error);
        this.isConnected = false;
      });

      this.client.on('close', () => {
        console.log('🔌 MQTT connection closed');
        this.isConnected = false;
      });

      this.client.on('reconnect', () => {
        console.log('🔄 MQTT reconnecting...');
      });

    } catch (error) {
      console.error('❌ Failed to start MQTT service:', error);
    }
  }

  async stop() {
    console.log('🛑 Stopping MQTT service...');
    
    if (this.client) {
      this.client.end();
      this.client = null;
    }
    
    this.isConnected = false;
    console.log('✅ MQTT service stopped');
  }

  private async handleMessage(topic: string, message: Buffer) {
    try {
      // Extract device ID from topic
      const deviceId = topic.split('/')[1];
      const hexMessage = message.toString('hex');
      
      console.log(`📨 Received MQTT message from ${deviceId}: ${hexMessage.substring(0, 50)}...`);

      // Store raw hex message in mqtt_data table
      await this.storeMqttData(deviceId, topic, hexMessage);

      // Decode and store in raw_data table
      await this.decodeAndStoreRawData(deviceId, hexMessage);

    } catch (error) {
      console.error('❌ Error processing MQTT message:', error);
    }
  }

  private async storeMqttData(deviceId: string, topic: string, hexMessage: string) {
    try {
      // Check if device exists, create if not
      await this.ensureDeviceExists(deviceId);

      // Store in mqtt_data table
      await prisma.mqttData.create({
        data: {
          deviceId: deviceId,
          deviceId_fk: deviceId,
          hexMessage: hexMessage,
          topic: topic,
          timestamp: new Date()
        }
      });

      console.log(`💾 Stored MQTT data for device ${deviceId}`);
    } catch (error) {
      console.error('❌ Error storing MQTT data:', error);
    }
  }

  private async decodeAndStoreRawData(deviceId: string, hexMessage: string) {
    try {
      // Decode hex message to structured data
      const decodedData = this.decodeHexMessage(hexMessage);
      
      if (decodedData) {
        // Store in raw_data table
        await prisma.rawData.create({
          data: {
            deviceId: deviceId,
            deviceId_fk: deviceId,
            timestamp: new Date(),
            ...decodedData
          }
        });

        console.log(`📊 Stored decoded data for device ${deviceId}`);
      }
    } catch (error) {
      console.error('❌ Error storing decoded data:', error);
    }
  }

  private decodeHexMessage(hexMessage: string): any {
    try {
      // Convert hex to buffer
      const buffer = Buffer.from(hexMessage, 'hex');
      
      // Basic UC300 message structure (adjust based on your protocol)
      const decoded: any = {};
      
      // Example decoding (adjust based on your actual protocol)
      if (buffer.length >= 20) {
        // Signal strength (bytes 0-1)
        decoded.signalStrength = buffer.readInt16BE(0);
        decoded.signalDbm = buffer.readInt16BE(2);
        
        // Counters (bytes 4-11)
        decoded.di1Counter = buffer.readInt32BE(4);
        decoded.di2Counter = buffer.readInt32BE(8);
        decoded.di3Counter = buffer.readInt32BE(12);
        decoded.di4Counter = buffer.readInt32BE(16);
        
        // Digital outputs (byte 20)
        if (buffer.length >= 21) {
          decoded.do1Enabled = buffer[20].toString();
        }
        
        // Analog inputs (bytes 21-28)
        if (buffer.length >= 29) {
          decoded.ai1Value = buffer.readFloatBE(21);
        }
        
        // Additional fields
        if (buffer.length >= 30) {
          decoded.mobileSignal = buffer[29];
        }
        
        if (buffer.length >= 31) {
          decoded.doutEnabled = buffer[30].toString();
        }
        
        // Set default values for required fields
        decoded.diMode = 'normal';
        decoded.ainMode = 'voltage';
        decoded.startFlag = 1;
        decoded.dataType = 1;
        decoded.length = buffer.length;
        decoded.version = 1;
        decoded.endFlag = 1;
      }
      
      return decoded;
    } catch (error) {
      console.error('❌ Error decoding hex message:', error);
      return null;
    }
  }

  private async ensureDeviceExists(deviceId: string) {
    try {
      const existingDevice = await prisma.device.findUnique({
        where: { id: deviceId }
      });

      if (!existingDevice) {
        await prisma.device.create({
          data: {
            id: deviceId,
            name: `Device ${deviceId}`,
            status: true,
            isConfigured: false
          }
        });
        console.log(`📱 Created new device: ${deviceId}`);
      }
    } catch (error) {
      console.error('❌ Error ensuring device exists:', error);
    }
  }

  // Get service status
  getStatus() {
    return {
      isConnected: this.isConnected,
      clientId: this.client?.options.clientId,
      broker: process.env.MQTT_BROKER
    };
  }

  // Manual message processing for testing
  async processTestMessage(deviceId: string, hexMessage: string) {
    console.log(`🧪 Processing test message for device ${deviceId}`);
    await this.storeMqttData(deviceId, 'test/topic', hexMessage);
    await this.decodeAndStoreRawData(deviceId, hexMessage);
  }
}

export const mqttService = new MqttService(); 