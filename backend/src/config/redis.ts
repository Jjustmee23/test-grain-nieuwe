import { createClient } from 'redis';
import { logger } from './logger';

// Redis client configuration
const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';

export const redisClient = createClient({
  url: redisUrl,
});

// Error handling
redisClient.on('error', (err) => {
  logger.error('Redis Client Error:', err);
});

redisClient.on('connect', () => {
  logger.info('Redis client connected');
});

redisClient.on('ready', () => {
  logger.info('Redis client ready');
});

redisClient.on('end', () => {
  logger.info('Redis client connection ended');
});

redisClient.on('reconnecting', () => {
  logger.warn('Redis client reconnecting');
});

// Connect to Redis
export const connectRedis = async () => {
  try {
    await redisClient.connect();
    logger.info('✅ Redis connection successful');
  } catch (error) {
    logger.error('❌ Redis connection failed:', error);
    throw error;
  }
};

// Redis helper functions
export const redisHelpers = {
  // Set with expiration
  setEx: async (key: string, value: any, ttlSeconds: number = 3600) => {
    try {
      const serializedValue = JSON.stringify(value);
      await redisClient.setEx(key, ttlSeconds, serializedValue);
      return true;
    } catch (error) {
      logger.error('Redis SET error:', error);
      return false;
    }
  },

  // Get and parse
  get: async <T = any>(key: string): Promise<T | null> => {
    try {
      const value = await redisClient.get(key);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      logger.error('Redis GET error:', error);
      return null;
    }
  },

  // Delete
  del: async (key: string) => {
    try {
      await redisClient.del(key);
      return true;
    } catch (error) {
      logger.error('Redis DEL error:', error);
      return false;
    }
  },

  // Check if key exists
  exists: async (key: string): Promise<boolean> => {
    try {
      const result = await redisClient.exists(key);
      return result === 1;
    } catch (error) {
      logger.error('Redis EXISTS error:', error);
      return false;
    }
  },

  // Increment counter
  incr: async (key: string): Promise<number> => {
    try {
      return await redisClient.incr(key);
    } catch (error) {
      logger.error('Redis INCR error:', error);
      return 0;
    }
  },

  // Set with no expiration
  set: async (key: string, value: any) => {
    try {
      const serializedValue = JSON.stringify(value);
      await redisClient.set(key, serializedValue);
      return true;
    } catch (error) {
      logger.error('Redis SET error:', error);
      return false;
    }
  },

  // Get all keys matching pattern
  keys: async (pattern: string): Promise<string[]> => {
    try {
      return await redisClient.keys(pattern);
    } catch (error) {
      logger.error('Redis KEYS error:', error);
      return [];
    }
  },

  // Hash operations
  hSet: async (key: string, field: string, value: any) => {
    try {
      const serializedValue = JSON.stringify(value);
      await redisClient.hSet(key, field, serializedValue);
      return true;
    } catch (error) {
      logger.error('Redis HSET error:', error);
      return false;
    }
  },

  hGet: async <T = any>(key: string, field: string): Promise<T | null> => {
    try {
      const value = await redisClient.hGet(key, field);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      logger.error('Redis HGET error:', error);
      return null;
    }
  },

  hGetAll: async <T = any>(key: string): Promise<Record<string, T> | null> => {
    try {
      const hash = await redisClient.hGetAll(key);
      const result: Record<string, T> = {};
      
      for (const [field, value] of Object.entries(hash)) {
        result[field] = JSON.parse(value);
      }
      
      return Object.keys(result).length > 0 ? result : null;
    } catch (error) {
      logger.error('Redis HGETALL error:', error);
      return null;
    }
  },

  // List operations
  lPush: async (key: string, ...values: any[]) => {
    try {
      const serializedValues = values.map(v => JSON.stringify(v));
      await redisClient.lPush(key, serializedValues);
      return true;
    } catch (error) {
      logger.error('Redis LPUSH error:', error);
      return false;
    }
  },

  lRange: async <T = any>(key: string, start: number = 0, stop: number = -1): Promise<T[]> => {
    try {
      const values = await redisClient.lRange(key, start, stop);
      return values.map(v => JSON.parse(v));
    } catch (error) {
      logger.error('Redis LRANGE error:', error);
      return [];
    }
  },
};

// Cache key generators
export const cacheKeys = {
  user: (userId: number) => `user:${userId}`,
  userSession: (userId: number) => `session:user:${userId}`,
  factory: (factoryId: number) => `factory:${factoryId}`,
  device: (deviceId: string) => `device:${deviceId}`,
  batch: (batchId: number) => `batch:${batchId}`,
  powerStatus: (deviceId: string) => `power:status:${deviceId}`,
  analytics: (type: string, period: string) => `analytics:${type}:${period}`,
  notifications: (userId: number) => `notifications:user:${userId}`,
  rateLimitUser: (userId: number) => `rateLimit:user:${userId}`,
  rateLimitIP: (ip: string) => `rateLimit:ip:${ip}`,
  twoFactorAttempts: (userId: number) => `2fa:attempts:${userId}`,
  passwordResetToken: (token: string) => `password:reset:${token}`,
  emailVerificationToken: (token: string) => `email:verify:${token}`,
};

// Redis health check
export const getRedisHealth = async () => {
  try {
    const startTime = Date.now();
    await redisClient.ping();
    const latency = Date.now() - startTime;

    const info = await redisClient.info();
    const memoryInfo = info.split('\n').find(line => line.startsWith('used_memory_human:'));
    const memoryUsage = memoryInfo ? memoryInfo.split(':')[1].trim() : 'unknown';

    return {
      status: 'healthy',
      latency: `${latency}ms`,
      memoryUsage,
      connected: true
    };
  } catch (error) {
    logger.error('Redis health check failed:', error);
    return {
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
      connected: false
    };
  }
};

// Initialize Redis connection only if REDIS_URL is set
if (process.env.REDIS_URL) {
  connectRedis().catch((error) => {
    logger.error('Failed to initialize Redis:', error);
    logger.warn('Continuing without Redis for development...');
  });
} else {
  logger.info('Redis disabled for development - no REDIS_URL configured');
} 