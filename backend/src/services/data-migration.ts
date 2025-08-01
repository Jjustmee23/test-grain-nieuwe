import { PrismaClient } from '@prisma/client';
import { Client } from 'pg';

const prisma = new PrismaClient();

// Counter database connection (source)
const counterDbClient = new Client({
  host: process.env.COUNTER_DB_HOST || 'localhost',
  port: parseInt(process.env.COUNTER_DB_PORT || '5432'),
  database: process.env.COUNTER_DB_NAME || 'counter_db',
  user: process.env.COUNTER_DB_USER || 'counter_user',
  password: process.env.COUNTER_DB_PASSWORD || 'counter_password',
});

class DataMigrationService {
  private isRunning = false;
  private interval: NodeJS.Timeout | null = null;

  async start() {
    console.log('🚀 Starting data migration service...');
    
    try {
      // Connect to counter database
      await counterDbClient.connect();
      console.log('✅ Connected to counter database');
      
      // Start migration every 5 minutes
      this.interval = setInterval(async () => {
        await this.migrateData();
      }, 5 * 60 * 1000); // 5 minutes
      
      // Run initial migration
      await this.migrateData();
      
      console.log('✅ Data migration service started successfully');
    } catch (error) {
      console.error('❌ Failed to start data migration service:', error);
    }
  }

  async stop() {
    console.log('🛑 Stopping data migration service...');
    
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    
    try {
      await counterDbClient.end();
      console.log('✅ Data migration service stopped');
    } catch (error) {
      console.error('❌ Error stopping data migration service:', error);
    }
  }

  async migrateData() {
    if (this.isRunning) {
      console.log('⏳ Migration already in progress, skipping...');
      return;
    }

    this.isRunning = true;
    
    try {
      console.log('📊 Starting data migration...');
      
      // Get the last migration timestamp
      const lastMigration = await this.getLastMigrationTimestamp();
      
      // Query new data from counter database
      const newData = await this.getNewDataFromCounter(lastMigration);
      
      if (newData.length === 0) {
        console.log('ℹ️ No new data to migrate');
        return;
      }
      
      console.log(`📈 Found ${newData.length} new records to migrate`);
      
      // Migrate data in batches
      const batchSize = 100;
      for (let i = 0; i < newData.length; i += batchSize) {
        const batch = newData.slice(i, i + batchSize);
        await this.migrateBatch(batch);
        console.log(`✅ Migrated batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(newData.length / batchSize)}`);
      }
      
      // Update last migration timestamp
      await this.updateLastMigrationTimestamp();
      
      console.log(`🎉 Data migration completed: ${newData.length} records migrated`);
      
    } catch (error) {
      console.error('❌ Data migration failed:', error);
    } finally {
      this.isRunning = false;
    }
  }

  private async getLastMigrationTimestamp(): Promise<Date> {
    try {
      // Get the latest timestamp from mill_rawdata
      const latestRecord = await prisma.rawData.findFirst({
        orderBy: { createdAt: 'desc' },
        select: { createdAt: true }
      });
      
      return latestRecord?.createdAt || new Date(0);
    } catch (error) {
      console.error('❌ Error getting last migration timestamp:', error);
      return new Date(0);
    }
  }

  private async getNewDataFromCounter(lastTimestamp: Date): Promise<any[]> {
    try {
      const query = `
        SELECT 
          device_id,
          timestamp,
          signal_strength,
          signal_dbm,
          di1_counter,
          di2_counter,
          di3_counter,
          di4_counter,
          do1_enabled,
          ai1_value
        FROM counter_data 
        WHERE timestamp > $1 
        ORDER BY timestamp ASC
      `;
      
      const result = await counterDbClient.query(query, [lastTimestamp]);
      return result.rows;
    } catch (error) {
      console.error('❌ Error querying counter database:', error);
      return [];
    }
  }

  private async migrateBatch(data: any[]) {
    try {
      const rawDataRecords = data.map(record => ({
        deviceId: record.device_id,
        timestamp: new Date(record.timestamp),
        signalStrength: record.signal_strength,
        signalDbm: record.signal_dbm,
        di1Counter: record.di1_counter,
        di2Counter: record.di2_counter,
        di3Counter: record.di3_counter,
        di4Counter: record.di4_counter,
        do1Enabled: record.do1_enabled,
        ai1Value: record.ai1_value ? parseFloat(record.ai1_value) : null,
        createdAt: new Date(record.timestamp)
      }));

      await prisma.rawData.createMany({
        data: rawDataRecords,
        skipDuplicates: true
      });
    } catch (error) {
      console.error('❌ Error migrating batch:', error);
      throw error;
    }
  }

  private async updateLastMigrationTimestamp() {
    try {
      // This could be stored in a separate table for tracking
      // For now, we'll use the latest record timestamp
      console.log('✅ Migration timestamp updated');
    } catch (error) {
      console.error('❌ Error updating migration timestamp:', error);
    }
  }

  // Manual migration method for testing
  async migrateNow() {
    console.log('🔄 Manual migration triggered...');
    await this.migrateData();
  }

  // Get migration status
  async getStatus() {
    try {
      const totalRecords = await prisma.rawData.count();
      const latestRecord = await prisma.rawData.findFirst({
        orderBy: { createdAt: 'desc' },
        select: { createdAt: true }
      });

      return {
        isRunning: this.isRunning,
        totalRecords,
        lastMigration: latestRecord?.createdAt,
        serviceStatus: this.interval ? 'active' : 'stopped'
      };
    } catch (error) {
      console.error('❌ Error getting migration status:', error);
      return { error: 'Failed to get status' };
    }
  }
}

export const dataMigrationService = new DataMigrationService(); 