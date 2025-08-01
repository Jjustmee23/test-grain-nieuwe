import winston from 'winston';
export declare const logger: winston.Logger;
export declare const morganStream: {
    write: (message: string) => void;
};
export declare const logWithMetadata: (level: string, message: string, metadata?: any) => void;
export declare const logError: (error: Error, context?: string, metadata?: any) => void;
export declare const logInfo: (message: string, metadata?: any) => void;
export declare const logWarn: (message: string, metadata?: any) => void;
export declare const logDebug: (message: string, metadata?: any) => void;
export declare const logHttp: (message: string, metadata?: any) => void;
//# sourceMappingURL=logger.d.ts.map