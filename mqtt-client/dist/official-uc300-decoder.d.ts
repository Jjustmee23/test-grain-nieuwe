export interface UC300Payload {
    startFlag: number;
    dataType: number;
    packetLength: number;
    endFlag: number;
    data: any;
}
export interface UC300RegularReport {
    version: number;
    timestamp: number;
    signalStrength: number;
    doutEnabled: boolean[];
    doutStatus: boolean[];
    diModes: number[];
    diStatus: boolean[];
    counterValues: number[];
    ainModes: number[];
    ainValues: number[];
    modbusData?: any[];
}
export interface UC300ChangeReport {
    version: number;
    timestamp: number;
    diModes: number[];
    diStatus: boolean[];
    counterValues: number[];
    doutEnabled: boolean[];
    doutStatus: boolean[];
}
export interface UC300AttributeReport {
    version: number;
    ucpVersion: string;
    serialNumber: string;
    hardwareVersion: string;
    firmwareVersion: string;
    imei: string;
    imsi: string;
    iccid: string;
}
export declare class OfficialUC300Decoder {
    /**
     * Decode UC300 payload according to official Milesight protocol
     */
    static decodePayload(buffer: Buffer): UC300Payload | null;
    /**
     * Decode F2: Change Report
     */
    private static decodeChangeReport;
    /**
     * Decode F3: Attribute Report
     */
    private static decodeAttributeReport;
    /**
     * Decode F4: Regular Report
     */
    private static decodeRegularReport;
    /**
     * Get human readable status
     */
    static getReadableStatus(payload: UC300Payload): any;
}
//# sourceMappingURL=official-uc300-decoder.d.ts.map