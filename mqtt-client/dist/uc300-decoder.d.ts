export interface UC300Payload {
    deviceId: string;
    timestamp: Date;
    status: string;
    rawData: Buffer;
    decodedData?: any;
}
export declare class UC300Decoder {
    /**
     * Decode UC300 status payload
     * @param deviceId - Device ID from topic
     * @param payload - Raw buffer payload
     * @returns Decoded UC300 payload
     */
    static decodeStatusPayload(deviceId: string, payload: Buffer): UC300Payload | null;
    /**
     * Find device ID in payload
     */
    private static findDeviceIdInPayload;
    /**
     * Extract counter values from payload
     */
    private static extractCounters;
    /**
     * Extract analog values from payload
     */
    private static extractAnalogValues;
    /**
     * Extract digital states from payload
     */
    private static extractDigitalStates;
    /**
     * Get human readable status
     */
    static getReadableStatus(payload: UC300Payload): {
        deviceId: string;
        timestamp: Date;
        status: string;
        hasDecodedData: boolean;
        decodedData: any;
    };
    /**
     * Analyze payload structure
     */
    static analyzePayload(payload: Buffer): any;
}
//# sourceMappingURL=uc300-decoder.d.ts.map