import { PrismaClient } from '@prisma/client';
import { logger } from './logger';

// Main Database (Django legacy) - testdb
export const prisma = new PrismaClient({
  datasources: {
    db: {
      url: `postgresql://${process.env.DB_USER}:${process.env.DB_PASSWORD}@${process.env.DB_HOST}:${process.env.DB_PORT}/${process.env.DB_NAME}`
    }
  }
});

// Counter Database (Hardware) - counter
export const counterPrisma = new PrismaClient({
  datasources: {
    db: {
      url: `postgresql://${process.env.COUNTER_DB_USER}:${process.env.COUNTER_DB_PASSWORD}@${process.env.COUNTER_DB_HOST}:${process.env.COUNTER_DB_PORT}/${process.env.COUNTER_DB_NAME}`
    }
  }
});

// Test database connections
export const testDatabaseConnections = async () => {
  try {
    logger.info('Testing database connections...');
    
    // Test main database
    await prisma.$queryRaw`SELECT 1 as test`;
    logger.info('✅ Main database connection successful');
    
    // Test counter database
    await counterPrisma.$queryRaw`SELECT 1 as test`;
    logger.info('✅ Counter database connection successful');
    
    return true;
  } catch (error) {
    logger.error('❌ Database connection failed:', error);
    throw error;
  }
};

// Database health check
export const getDatabaseHealth = async () => {
  try {
    const mainDbStart = Date.now();
    await prisma.$queryRaw`SELECT 1 as test`;
    const mainDbLatency = Date.now() - mainDbStart;

    const counterDbStart = Date.now();
    await counterPrisma.$queryRaw`SELECT 1 as test`;
    const counterDbLatency = Date.now() - counterDbStart;

    return {
      status: 'healthy',
      mainDatabase: {
        status: 'connected',
        latency: `${mainDbLatency}ms`,
        host: process.env.DB_HOST,
        port: process.env.DB_PORT,
        database: process.env.DB_NAME
      },
      counterDatabase: {
        status: 'connected',
        latency: `${counterDbLatency}ms`,
        host: process.env.COUNTER_DB_HOST,
        port: process.env.COUNTER_DB_PORT,
        database: process.env.COUNTER_DB_NAME
      }
    };
  } catch (error) {
    logger.error('Database health check failed:', error);
    return {
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
};

// Graceful shutdown
export const closeDatabaseConnections = async () => {
  try {
    await prisma.$disconnect();
    await counterPrisma.$disconnect();
    logger.info('Database connections closed successfully');
  } catch (error) {
    logger.error('Error closing database connections:', error);
  }
}; 