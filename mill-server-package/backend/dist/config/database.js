"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.closeDatabaseConnections = exports.getDatabaseHealth = exports.testDatabaseConnections = exports.counterPrisma = exports.prisma = void 0;
const client_1 = require("@prisma/client");
const logger_1 = require("./logger");
exports.prisma = new client_1.PrismaClient({
    log: [
        {
            emit: 'event',
            level: 'query',
        },
        {
            emit: 'event',
            level: 'error',
        },
        {
            emit: 'event',
            level: 'info',
        },
        {
            emit: 'event',
            level: 'warn',
        },
    ],
});
exports.counterPrisma = new client_1.PrismaClient({
    datasources: {
        db: {
            url: process.env.COUNTER_DATABASE_URL
        }
    },
    log: [
        {
            emit: 'event',
            level: 'error',
        },
    ],
});
exports.prisma.$on('query', (e) => {
    if (process.env.NODE_ENV === 'development') {
        logger_1.logger.debug(`Query: ${e.query}`);
        logger_1.logger.debug(`Params: ${e.params}`);
        logger_1.logger.debug(`Duration: ${e.duration}ms`);
    }
});
exports.prisma.$on('error', (e) => {
    logger_1.logger.error('Database error:', e);
});
exports.prisma.$on('info', (e) => {
    logger_1.logger.info('Database info:', e.message);
});
exports.prisma.$on('warn', (e) => {
    logger_1.logger.warn('Database warning:', e.message);
});
exports.counterPrisma.$on('error', (e) => {
    logger_1.logger.error('Counter database error:', e);
});
const testDatabaseConnections = async () => {
    try {
        await exports.prisma.$queryRaw `SELECT 1`;
        logger_1.logger.info('✅ Main database connection successful');
        await exports.counterPrisma.$queryRaw `SELECT 1`;
        logger_1.logger.info('✅ Counter database connection successful');
        return true;
    }
    catch (error) {
        logger_1.logger.error('❌ Database connection failed:', error);
        throw error;
    }
};
exports.testDatabaseConnections = testDatabaseConnections;
const getDatabaseHealth = async () => {
    try {
        const startTime = Date.now();
        await exports.prisma.$queryRaw `SELECT 1`;
        const mainDbLatency = Date.now() - startTime;
        const counterStartTime = Date.now();
        await exports.counterPrisma.$queryRaw `SELECT 1`;
        const counterDbLatency = Date.now() - counterStartTime;
        return {
            status: 'healthy',
            mainDatabase: {
                status: 'connected',
                latency: `${mainDbLatency}ms`
            },
            counterDatabase: {
                status: 'connected',
                latency: `${counterDbLatency}ms`
            }
        };
    }
    catch (error) {
        logger_1.logger.error('Database health check failed:', error);
        return {
            status: 'unhealthy',
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
};
exports.getDatabaseHealth = getDatabaseHealth;
const closeDatabaseConnections = async () => {
    try {
        await exports.prisma.$disconnect();
        await exports.counterPrisma.$disconnect();
        logger_1.logger.info('Database connections closed successfully');
    }
    catch (error) {
        logger_1.logger.error('Error closing database connections:', error);
    }
};
exports.closeDatabaseConnections = closeDatabaseConnections;
//# sourceMappingURL=database.js.map