export interface MilsightPayload {
    startFlag: number;
    dataType: number;
    length: number;
    version: number;
    deviceId: string;
    doutEnabled: string;
    dout: string;
    diMode: string;
    din: string;
    counter1: number;
    counter2: number;
    counter3: number;
    counter4: number;
    ainMode: string;
    ain1Value: number;
    ain2Value: number;
    ain3Value: number;
    ain4Value: number;
    ain5Value: number;
    ain6Value: number;
    ain7Value: number;
    ain8Value: number;
    mobileSignal: number;
    endFlag: number;
    timestamp: Date;
}
export declare class MilsightDecoder {
    /**
     * Decode hex payload from UC300 device
     * @param hexPayload - Raw hex string from MQTT
     * @returns Decoded Milsight payload
     */
    static decodeHexPayload(hexPayload: string): MilsightPayload | null;
    /**
     * Convert raw analog value to voltage/temperature
     * @param rawValue - Raw 32-bit analog value
     * @returns Converted value
     */
    private static convertAnalogValue;
    /**
     * Parse digital input/output states
     * @param binaryString - Binary string representation
     * @returns Array of boolean states
     */
    static parseDigitalStates(binaryString: string): boolean[];
    /**
     * Get human readable status
     * @param payload - Decoded payload
     * @returns Human readable status object
     */
    static getReadableStatus(payload: MilsightPayload): {
        deviceId: string;
        timestamp: Date;
        mobileSignal: string;
        digitalInputs: {
            input1: boolean;
            input2: boolean;
            input3: boolean;
            input4: boolean;
            input5: boolean;
            input6: boolean;
            input7: boolean;
            input8: boolean;
        };
        digitalOutputs: {
            output1: boolean;
            output2: boolean;
            output3: boolean;
            output4: boolean;
            output5: boolean;
            output6: boolean;
            output7: boolean;
            output8: boolean;
        };
        counters: {
            counter1: number;
            counter2: number;
            counter3: number;
            counter4: number;
        };
        analogInputs: {
            ain1: string;
            ain2: string;
            ain3: string;
            ain4: string;
            ain5: string;
            ain6: string;
            ain7: string;
            ain8: string;
        };
    };
    /**
     * Validate payload structure
     * @param payload - Decoded payload
     * @returns Validation result
     */
    static validatePayload(payload: MilsightPayload): {
        valid: boolean;
        errors: string[];
    };
}
//# sourceMappingURL=milsight-decoder.d.ts.map