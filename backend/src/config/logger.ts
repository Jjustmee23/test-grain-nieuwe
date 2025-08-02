import winston from 'winston';
import path from 'path';

// Define custom log levels
const customLevels = {
  levels: {
    error: 0,
    warn: 1,
    info: 2,
    http: 3,
    debug: 4,
  },
  colors: {
    error: 'red',
    warn: 'yellow',
    info: 'green',
    http: 'magenta',
    debug: 'blue',
  },
};

// Add colors to winston
winston.addColors(customLevels.colors);

// Create logs directory if it doesn't exist
const logsDir = path.join(process.cwd(), 'logs');

// Define log format
const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.prettyPrint()
);

// Console format for development
const consoleFormat = winston.format.combine(
  winston.format.colorize({ all: true }),
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    let msg = `${timestamp} [${level}]: ${message}`;
    
    // Add metadata if present
    if (Object.keys(meta).length > 0) {
      msg += `\n${JSON.stringify(meta, null, 2)}`;
    }
    
    return msg;
  })
);

// Create the logger
export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  levels: customLevels.levels,
  format: logFormat,
  defaultMeta: { 
    service: 'mill-management-api',
    version: process.env.npm_package_version || '1.0.0'
  },
  transports: [
    // Console transport for all environments
    new winston.transports.Console({
      format: consoleFormat,
      level: 'debug'
    }),

    // File transports only in development
    ...(process.env.NODE_ENV === 'development' ? [
      new winston.transports.File({
        filename: path.join(logsDir, 'error.log'),
        level: 'error',
        maxsize: 5242880, // 5MB
        maxFiles: 5,
      }),
      new winston.transports.File({
        filename: path.join(logsDir, 'combined.log'),
        maxsize: 5242880, // 5MB
        maxFiles: 5,
      }),
      new winston.transports.File({
        filename: path.join(logsDir, 'http.log'),
        level: 'http',
        maxsize: 5242880, // 5MB
        maxFiles: 3,
      }),
    ] : []),
  ],
  exceptionHandlers: [
    // Console exception handler for production
    new winston.transports.Console({
      format: consoleFormat,
    }),
    // File exception handler only in development
    ...(process.env.NODE_ENV === 'development' ? [
      new winston.transports.File({
        filename: path.join(logsDir, 'exceptions.log'),
        maxsize: 5242880, // 5MB
        maxFiles: 3,
      }),
    ] : []),
  ],
  rejectionHandlers: [
    // Console rejection handler for production
    new winston.transports.Console({
      format: consoleFormat,
    }),
    // File rejection handler only in development
    ...(process.env.NODE_ENV === 'development' ? [
      new winston.transports.File({
        filename: path.join(logsDir, 'rejections.log'),
        maxsize: 5242880, // 5MB
        maxFiles: 3,
      }),
    ] : []),
  ],
});

// Create a stream for Morgan HTTP logging
export const morganStream = {
  write: (message: string) => {
    logger.http(message.trim());
  },
};

// Helper functions for structured logging
export const logWithMetadata = (level: string, message: string, metadata: any = {}) => {
  logger.log(level, message, {
    ...metadata,
    timestamp: new Date().toISOString(),
  });
};

export const logError = (error: Error, context?: string, metadata: any = {}) => {
  logger.error(`${context ? `[${context}] ` : ''}${error.message}`, {
    error: {
      name: error.name,
      message: error.message,
      stack: error.stack,
    },
    ...metadata,
  });
};

export const logInfo = (message: string, metadata: any = {}) => {
  logWithMetadata('info', message, metadata);
};

export const logWarn = (message: string, metadata: any = {}) => {
  logWithMetadata('warn', message, metadata);
};

export const logDebug = (message: string, metadata: any = {}) => {
  logWithMetadata('debug', message, metadata);
};

export const logHttp = (message: string, metadata: any = {}) => {
  logWithMetadata('http', message, metadata);
};

// Production-specific configuration
if (process.env.NODE_ENV === 'production') {
  // Add CloudWatch or other production log transports here
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.json()
    ),
    level: 'info'
  }));
} 