export declare const prisma: any;
export declare const counterPrisma: any;
export declare const testDatabaseConnections: () => Promise<boolean>;
export declare const getDatabaseHealth: () => Promise<{
    status: string;
    mainDatabase: {
        status: string;
        latency: string;
    };
    counterDatabase: {
        status: string;
        latency: string;
    };
    error?: undefined;
} | {
    status: string;
    error: string;
    mainDatabase?: undefined;
    counterDatabase?: undefined;
}>;
export declare const closeDatabaseConnections: () => Promise<void>;
//# sourceMappingURL=database.d.ts.map