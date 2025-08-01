"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createValidationError = exports.notFoundHandler = exports.asyncHandler = exports.errorHandler = exports.createError = exports.AppError = void 0;
const client_1 = require("@prisma/client");
const logger_1 = require("../config/logger");
class AppError extends Error {
    statusCode;
    isOperational;
    constructor(message, statusCode = 500, isOperational = true) {
        super(message);
        this.statusCode = statusCode;
        this.isOperational = isOperational;
        Error.captureStackTrace(this, this.constructor);
    }
}
exports.AppError = AppError;
const createError = (message, statusCode = 500) => {
    return new AppError(message, statusCode);
};
exports.createError = createError;
const errorHandler = (error, req, res, next) => {
    let statusCode = error.statusCode || 500;
    let message = error.message || 'Internal Server Error';
    let details = null;
    logger_1.logger.error('Error occurred:', {
        error: {
            name: error.name,
            message: error.message,
            stack: error.stack,
            statusCode
        },
        request: {
            method: req.method,
            url: req.originalUrl,
            ip: req.ip,
            userAgent: req.get('User-Agent')
        }
    });
    if (error instanceof client_1.Prisma.PrismaClientKnownRequestError) {
        switch (error.code) {
            case 'P2002':
                statusCode = 409;
                message = 'Resource already exists';
                details = {
                    field: error.meta?.target,
                    constraint: 'unique_violation'
                };
                break;
            case 'P2025':
                statusCode = 404;
                message = 'Resource not found';
                break;
            case 'P2003':
                statusCode = 400;
                message = 'Invalid reference to related resource';
                details = {
                    field: error.meta?.field_name,
                    constraint: 'foreign_key_violation'
                };
                break;
            case 'P2014':
                statusCode = 400;
                message = 'Required relation is missing';
                break;
            default:
                statusCode = 400;
                message = 'Database operation failed';
                details = {
                    code: error.code,
                    meta: error.meta
                };
        }
    }
    else if (error instanceof client_1.Prisma.PrismaClientValidationError) {
        statusCode = 400;
        message = 'Invalid data provided';
        details = {
            type: 'validation_error',
            hint: 'Check your input data format and types'
        };
    }
    else if (error instanceof client_1.Prisma.PrismaClientInitializationError) {
        statusCode = 500;
        message = 'Database connection failed';
        details = {
            type: 'database_error',
            hint: 'Please try again later'
        };
    }
    else if (error instanceof SyntaxError && 'body' in error) {
        statusCode = 400;
        message = 'Invalid JSON format';
        details = {
            type: 'json_parse_error',
            hint: 'Check your JSON syntax'
        };
    }
    else if (error.name === 'ValidationError' && error.errors) {
        statusCode = 400;
        message = 'Validation failed';
        details = {
            type: 'validation_error',
            errors: error.errors
        };
    }
    else if (error.name === 'JsonWebTokenError') {
        statusCode = 401;
        message = 'Invalid authentication token';
    }
    else if (error.name === 'TokenExpiredError') {
        statusCode = 401;
        message = 'Authentication token expired';
    }
    else if (error.name === 'MulterError') {
        statusCode = 400;
        switch (error.code) {
            case 'LIMIT_FILE_SIZE':
                message = 'File too large';
                break;
            case 'LIMIT_FILE_COUNT':
                message = 'Too many files';
                break;
            case 'LIMIT_UNEXPECTED_FILE':
                message = 'Unexpected file field';
                break;
            default:
                message = 'File upload error';
        }
    }
    const sendStackTrace = process.env.NODE_ENV === 'development' && statusCode >= 500;
    const errorResponse = {
        error: message,
        status: statusCode,
        timestamp: new Date().toISOString(),
        path: req.originalUrl,
        method: req.method
    };
    if (details) {
        errorResponse.details = details;
    }
    if (sendStackTrace) {
        errorResponse.stack = error.stack;
    }
    if (req.headers['x-request-id']) {
        errorResponse.requestId = req.headers['x-request-id'];
    }
    if (process.env.NODE_ENV === 'production') {
        if (statusCode >= 500) {
            errorResponse.error = 'Internal server error';
            delete errorResponse.details;
        }
    }
    res.status(statusCode).json(errorResponse);
};
exports.errorHandler = errorHandler;
const asyncHandler = (fn) => {
    return (req, res, next) => {
        Promise.resolve(fn(req, res, next)).catch(next);
    };
};
exports.asyncHandler = asyncHandler;
const notFoundHandler = (req, res) => {
    const error = new AppError(`Route ${req.originalUrl} not found`, 404);
    res.status(404).json({
        error: error.message,
        status: 404,
        timestamp: new Date().toISOString(),
        path: req.originalUrl,
        method: req.method
    });
};
exports.notFoundHandler = notFoundHandler;
const createValidationError = (errors) => {
    const error = new AppError('Validation failed', 400);
    error.errors = errors;
    error.name = 'ValidationError';
    return error;
};
exports.createValidationError = createValidationError;
//# sourceMappingURL=errorHandler.js.map