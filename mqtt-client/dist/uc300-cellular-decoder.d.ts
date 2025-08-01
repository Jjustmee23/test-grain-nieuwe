export interface UC300CellularPayload {
    deviceId: string;
    timestamp: Date;
    messageType: 'status' | 'online' | 'offline' | 'data';
    signalStrength?: number;
    networkType?: string;
    imei?: string;
    counters?: number[];
    analogInputs?: number[];
    digitalInputs?: boolean[];
    digitalOutputs?: boolean[];
    rawHex: string;
    payloadLength: number;
}
export declare class UC300CellularDecoder {
    /**
     * Decode UC300 Cellular payload with high performance
     * @param deviceId - Device ID from topic
     * @param payload - Raw buffer payload
     * @returns Decoded cellular payload
     */
    static decodeCellularPayload(deviceId: string, payload: Buffer): UC300CellularPayload | null;
    /**
     * Convert raw analog value to voltage
     */
    private static convertToVoltage;
    /**
     * Convert byte to array of bits
     */
    private static byteToBits;
    /**
     * Get network type from byte
     */
    private static getNetworkType;
    /**
     * Get human readable status
     */
    static getReadableStatus(payload: UC300CellularPayload): {
        deviceId: string;
        timestamp: Date;
        messageType: "data" | "offline" | "status" | "online";
        cellular: {
            signalStrength: string;
            networkType: string;
            imei: string;
        };
        data: {
            counters: number[];
            analogInputs: number[];
            digitalInputs: boolean[];
            digitalOutputs: boolean[];
        };
    };
    /**
     * Validate payload for cellular format
     */
    static validateCellularPayload(payload: UC300CellularPayload): {
        valid: boolean;
        errors: string[];
    };
}
//# sourceMappingURL=uc300-cellular-decoder.d.ts.map