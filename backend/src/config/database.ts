import { PrismaClient } from '@prisma/client';
import { logger } from './logger';

// Local PostgreSQL Database
export const prisma = new PrismaClient({
  datasources: {
    db: {
      url: `postgresql://${process.env.DB_USER}:${process.env.DB_PASSWORD}@${process.env.DB_HOST}:${process.env.DB_PORT}/${process.env.DB_NAME}`
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

    return {
      status: 'healthy',
      database: {
        status: 'connected',
        latency: `${latency}ms`,
        host: process.env.DB_HOST,
        port: process.env.DB_PORT,
        database: process.env.DB_NAME
      }
    };
  } catch (error) {
    logger.error('Error getting database health:', error);
    return {
      status: 'unhealthy',
      database: { 
        status: 'disconnected', 
        latency: 'N/A', 
        host: process.env.DB_HOST, 
        port: process.env.DB_PORT, 
        database: process.env.DB_NAME 
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