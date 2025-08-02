export interface MilesightIPSOData {
    deviceId: string;
    timestamp: Date;
    fPort: number;
    uplinkType: 'attribute-report' | 'regular-report';
    protocolVersion?: string;
    hardwareVersion?: string;
    firmwareVersion?: string;
    powerOnTime?: number;
    serialNumber?: string;
    digitalInputs: boolean[];
    digitalOutputs: boolean[];
    analogInputs: {
        [key: string]: number;
    };
    pt100Temperatures: {
        [key: string]: number;
    };
    modbusData?: any;
    rawPayload: Buffer;
    decodedChannels: {
        [channel: string]: any;
    };
}
export declare class MilesightIPSODecoder {
    /**
     * Decode Milesight IPSO payload
     * @param deviceId - Device ID from topic
     * @param payload - Raw buffer payload
     * @param fPort - fPort number (should be 85 for UC300)
     * @returns Decoded IPSO data
     */
    static decodeIPSO(deviceId: string, payload: Buffer, fPort?: number): MilesightIPSOData | null;
    /**
     * Decode individual channel
     */
    private static decodeChannel;
    /**
     * Decode FF channels (device information)
     */
    private static decodeFFChannel;
    /**
     * Decode Digital Input (channels 03-06)
     */
    private static decodeDigitalInput;
    /**
     * Decode Digital Output (channels 07-08)
     */
    private static decodeDigitalOutput;
    /**
     * Decode PT100 Temperature (channels 09-0A)
     */
    private static decodePT100;
    /**
     * Decode Analog Input (channels 0B-0E)
     */
    private static decodeAnalogInput;
    /**
     * Decode Modbus Data (channel FF 19)
     */
    private static decodeModbusData;
    /**
     * Store decoded channel data in main object
     */
    private static storeChannelData;
    /**
     * Get human readable status
     */
    static getReadableStatus(data: MilesightIPSOData): {
        deviceId: string;
        timestamp: Date;
        fPort: number;
        uplinkType: "attribute-report" | "regular-report";
        deviceInfo: {
            protocolVersion: string | undefined;
            hardwareVersion: string | undefined;
            firmwareVersion: string | undefined;
            powerOnTime: number | undefined;
            serialNumber: string | undefined;
        };
        sensors: {
            digitalInputs: {
                [x: string]: string;
            }[];
            digitalOutputs: {
                [x: string]: string;
            }[];
            analogInputs: {
                [key: string]: number;
            };
            pt100Temperatures: {
                [key: string]: number;
            };
        };
        modbus: any;
        decodedChannels: {
            [channel: string]: any;
        };
    };
}
//# sourceMappingURL=milesight-ipso-decoder.d.ts.map