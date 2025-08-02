import { PrismaClient } from '@prisma/client';
import { logger } from './logger';

// Local PostgreSQL Database
export const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL
    }
  }
});

// Test database connection
export const testDatabaseConnections = async () => {
  try {
    logger.info('Testing database connection...');
    
    // Test local database
    await prisma.$queryRaw`SELECT 1 as test`;
    logger.info('✅ Local database connection successful');
    
    return true;
  } catch (error) {
    logger.error('❌ Database connection failed:', error);
    throw error;
  }
};

export const getDatabaseHealth = async () => {
  try {
    const start = Date.now();
    await prisma.$queryRaw`SELECT 1 as test`;
    const latency = Date.now() - start;

    // Parse DATABASE_URL to get connection details
    const dbUrl = process.env.DATABASE_URL || '';
    const urlMatch = dbUrl.match(/postgresql:\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/([^?]+)/);
    
    const host = urlMatch ? urlMatch[3] : 'unknown';
    const port = urlMatch ? urlMatch[4] : 'unknown';
    const database = urlMatch ? urlMatch[5] : 'unknown';

    return {
      status: 'healthy',
      database: {
        status: 'connected',
        latency: `${latency}ms`,
        host,
        port,
        database
      }
    };
  } catch (error) {
    logger.error('Error getting database health:', error);
    
    // Parse DATABASE_URL to get connection details
    const dbUrl = process.env.DATABASE_URL || '';
    const urlMatch = dbUrl.match(/postgresql:\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/([^?]+)/);
    
    const host = urlMatch ? urlMatch[3] : 'unknown';
    const port = urlMatch ? urlMatch[4] : 'unknown';
    const database = urlMatch ? urlMatch[5] : 'unknown';

    return {
      status: 'unhealthy',
      database: { 
        status: 'disconnected', 
        latency: 'N/A', 
        host, 
        port, 
        database 
      }
    };
  }
};

export const closeDatabaseConnections = async () => {
  try {
    await prisma.$disconnect();
    logger.info('Database connections closed successfully');
  } catch (error) {
    logger.error('Error closing database connections:', error);
  }
}; 