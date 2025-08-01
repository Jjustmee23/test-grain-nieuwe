"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.logHttp = exports.logDebug = exports.logWarn = exports.logInfo = exports.logError = exports.logWithMetadata = exports.morganStream = exports.logger = void 0;
const winston_1 = __importDefault(require("winston"));
const path_1 = __importDefault(require("path"));
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
winston_1.default.addColors(customLevels.colors);
const logsDir = path_1.default.join(process.cwd(), 'logs');
const logFormat = winston_1.default.format.combine(winston_1.default.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }), winston_1.default.format.errors({ stack: true }), winston_1.default.format.json(), winston_1.default.format.prettyPrint());
const consoleFormat = winston_1.default.format.combine(winston_1.default.format.colorize({ all: true }), winston_1.default.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }), winston_1.default.format.printf(({ timestamp, level, message, ...meta }) => {
    let msg = `${timestamp} [${level}]: ${message}`;
    if (Object.keys(meta).length > 0) {
        msg += `\n${JSON.stringify(meta, null, 2)}`;
    }
    return msg;
}));
exports.logger = winston_1.default.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    levels: customLevels.levels,
    format: logFormat,
    defaultMeta: {
        service: 'mill-management-api',
        version: process.env.npm_package_version || '1.0.0'
    },
    transports: [
        ...(process.env.NODE_ENV !== 'production' ? [
            new winston_1.default.transports.Console({
                format: consoleFormat,
                level: 'debug'
            })
        ] : []),
        new winston_1.default.transports.File({
            filename: path_1.default.join(logsDir, 'error.log'),
            level: 'error',
            maxsize: 5242880,
            maxFiles: 5,
        }),
        new winston_1.default.transports.File({
            filename: path_1.default.join(logsDir, 'combined.log'),
            maxsize: 5242880,
            maxFiles: 5,
        }),
        new winston_1.default.transports.File({
            filename: path_1.default.join(logsDir, 'http.log'),
            level: 'http',
            maxsize: 5242880,
            maxFiles: 3,
        }),
    ],
    exceptionHandlers: [
        new winston_1.default.transports.File({
            filename: path_1.default.join(logsDir, 'exceptions.log'),
            maxsize: 5242880,
            maxFiles: 3,
        }),
    ],
    rejectionHandlers: [
        new winston_1.default.transports.File({
            filename: path_1.default.join(logsDir, 'rejections.log'),
            maxsize: 5242880,
            maxFiles: 3,
        }),
    ],
});
exports.morganStream = {
    write: (message) => {
        exports.logger.http(message.trim());
    },
};
const logWithMetadata = (level, message, metadata = {}) => {
    exports.logger.log(level, message, {
        ...metadata,
        timestamp: new Date().toISOString(),
    });
};
exports.logWithMetadata = logWithMetadata;
const logError = (error, context, metadata = {}) => {
    exports.logger.error(`${context ? `[${context}] ` : ''}${error.message}`, {
        error: {
            name: error.name,
            message: error.message,
            stack: error.stack,
        },
        ...metadata,
    });
};
exports.logError = logError;
const logInfo = (message, metadata = {}) => {
    (0, exports.logWithMetadata)('info', message, metadata);
};
exports.logInfo = logInfo;
const logWarn = (message, metadata = {}) => {
    (0, exports.logWithMetadata)('warn', message, metadata);
};
exports.logWarn = logWarn;
const logDebug = (message, metadata = {}) => {
    (0, exports.logWithMetadata)('debug', message, metadata);
};
exports.logDebug = logDebug;
const logHttp = (message, metadata = {}) => {
    (0, exports.logWithMetadata)('http', message, metadata);
};
exports.logHttp = logHttp;
if (process.env.NODE_ENV === 'production') {
    exports.logger.add(new winston_1.default.transports.Console({
        format: winston_1.default.format.combine(winston_1.default.format.timestamp(), winston_1.default.format.json()),
        level: 'info'
    }));
}
//# sourceMappingURL=logger.js.map