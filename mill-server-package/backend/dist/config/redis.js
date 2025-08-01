"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getRedisHealth = exports.cacheKeys = exports.redisHelpers = exports.connectRedis = exports.redisClient = void 0;
const redis_1 = require("redis");
const logger_1 = require("./logger");
const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
exports.redisClient = (0, redis_1.createClient)({
    url: redisUrl,
});
exports.redisClient.on('error', (err) => {
    logger_1.logger.error('Redis Client Error:', err);
});
exports.redisClient.on('connect', () => {
    logger_1.logger.info('Redis client connected');
});
exports.redisClient.on('ready', () => {
    logger_1.logger.info('Redis client ready');
});
exports.redisClient.on('end', () => {
    logger_1.logger.info('Redis client connection ended');
});
exports.redisClient.on('reconnecting', () => {
    logger_1.logger.warn('Redis client reconnecting');
});
const connectRedis = async () => {
    try {
        await exports.redisClient.connect();
        logger_1.logger.info('✅ Redis connection successful');
    }
    catch (error) {
        logger_1.logger.error('❌ Redis connection failed:', error);
        throw error;
    }
};
exports.connectRedis = connectRedis;
exports.redisHelpers = {
    setEx: async (key, value, ttlSeconds = 3600) => {
        try {
            const serializedValue = JSON.stringify(value);
            await exports.redisClient.setEx(key, ttlSeconds, serializedValue);
            return true;
        }
        catch (error) {
            logger_1.logger.error('Redis SET error:', error);
            return false;
        }
    },
    get: async (key) => {
        try {
            const value = await exports.redisClient.get(key);
            return value ? JSON.parse(value) : null;
        }
        catch (error) {
            logger_1.logger.error('Redis GET error:', error);
            return null;
        }
    },
    del: async (key) => {
        try {
            await exports.redisClient.del(key);
            return true;
        }
        catch (error) {
            logger_1.logger.error('Redis DEL error:', error);
            return false;
        }
    },
    exists: async (key) => {
        try {
            const result = await exports.redisClient.exists(key);
            return result === 1;
        }
        catch (error) {
            logger_1.logger.error('Redis EXISTS error:', error);
            return false;
        }
    },
    incr: async (key) => {
        try {
            return await exports.redisClient.incr(key);
        }
        catch (error) {
            logger_1.logger.error('Redis INCR error:', error);
            return 0;
        }
    },
    set: async (key, value) => {
        try {
            const serializedValue = JSON.stringify(value);
            await exports.redisClient.set(key, serializedValue);
            return true;
        }
        catch (error) {
            logger_1.logger.error('Redis SET error:', error);
            return false;
        }
    },
    keys: async (pattern) => {
        try {
            return await exports.redisClient.keys(pattern);
        }
        catch (error) {
            logger_1.logger.error('Redis KEYS error:', error);
            return [];
        }
    },
    hSet: async (key, field, value) => {
        try {
            const serializedValue = JSON.stringify(value);
            await exports.redisClient.hSet(key, field, serializedValue);
            return true;
        }
        catch (error) {
            logger_1.logger.error('Redis HSET error:', error);
            return false;
        }
    },
    hGet: async (key, field) => {
        try {
            const value = await exports.redisClient.hGet(key, field);
            return value ? JSON.parse(value) : null;
        }
        catch (error) {
            logger_1.logger.error('Redis HGET error:', error);
            return null;
        }
    },
    hGetAll: async (key) => {
        try {
            const hash = await exports.redisClient.hGetAll(key);
            const result = {};
            for (const [field, value] of Object.entries(hash)) {
                result[field] = JSON.parse(value);
            }
            return Object.keys(result).length > 0 ? result : null;
        }
        catch (error) {
            logger_1.logger.error('Redis HGETALL error:', error);
            return null;
        }
    },
    lPush: async (key, ...values) => {
        try {
            const serializedValues = values.map(v => JSON.stringify(v));
            await exports.redisClient.lPush(key, serializedValues);
            return true;
        }
        catch (error) {
            logger_1.logger.error('Redis LPUSH error:', error);
            return false;
        }
    },
    lRange: async (key, start = 0, stop = -1) => {
        try {
            const values = await exports.redisClient.lRange(key, start, stop);
            return values.map(v => JSON.parse(v));
        }
        catch (error) {
            logger_1.logger.error('Redis LRANGE error:', error);
            return [];
        }
    },
};
exports.cacheKeys = {
    user: (userId) => `user:${userId}`,
    userSession: (userId) => `session:user:${userId}`,
    factory: (factoryId) => `factory:${factoryId}`,
    device: (deviceId) => `device:${deviceId}`,
    batch: (batchId) => `batch:${batchId}`,
    powerStatus: (deviceId) => `power:status:${deviceId}`,
    analytics: (type, period) => `analytics:${type}:${period}`,
    notifications: (userId) => `notifications:user:${userId}`,
    rateLimitUser: (userId) => `rateLimit:user:${userId}`,
    rateLimitIP: (ip) => `rateLimit:ip:${ip}`,
    twoFactorAttempts: (userId) => `2fa:attempts:${userId}`,
    passwordResetToken: (token) => `password:reset:${token}`,
    emailVerificationToken: (token) => `email:verify:${token}`,
};
const getRedisHealth = async () => {
    try {
        const startTime = Date.now();
        await exports.redisClient.ping();
        const latency = Date.now() - startTime;
        const info = await exports.redisClient.info();
        const memoryInfo = info.split('\n').find(line => line.startsWith('used_memory_human:'));
        const memoryUsage = memoryInfo ? memoryInfo.split(':')[1].trim() : 'unknown';
        return {
            status: 'healthy',
            latency: `${latency}ms`,
            memoryUsage,
            connected: true
        };
    }
    catch (error) {
        logger_1.logger.error('Redis health check failed:', error);
        return {
            status: 'unhealthy',
            error: error instanceof Error ? error.message : 'Unknown error',
            connected: false
        };
    }
};
exports.getRedisHealth = getRedisHealth;
(0, exports.connectRedis)().catch((error) => {
    logger_1.logger.error('Failed to initialize Redis:', error);
    process.exit(1);
});
//# sourceMappingURL=redis.js.map