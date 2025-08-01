// UC300 Cellular Version Decoder
// Optimized for high throughput: 300+ devices sending data every 5 minutes

export interface UC300CellularPayload {
  deviceId: string;
  timestamp: Date;
  messageType: 'status' | 'online' | 'offline' | 'data';
  
  // Cellular specific fields
  signalStrength?: number;
  networkType?: string;
  imei?: string;
  
  // Device data
  counters?: number[];
  analogInputs?: number[];
  digitalInputs?: boolean[];
  digitalOutputs?: boolean[];
  
  // Raw data for debugging
  rawHex: string;
  payloadLength: number;
}

export class UC300CellularDecoder {
  
  /**
   * Decode UC300 Cellular payload with high performance
   * @param deviceId - Device ID from topic
   * @param payload - Raw buffer payload
   * @returns Decoded cellular payload
   */
  static decodeCellularPayload(deviceId: string, payload: Buffer): UC300CellularPayload | null {
    try {
      const payloadHex = payload.toString('hex').toUpperCase();
      const payloadLength = payload.length;
      
      // Fast validation
      if (payloadLength < 10) {
        return null;
      }
      
      const decoded: UC300CellularPayload = {
        deviceId,
        timestamp: new Date(),
        messageType: 'data',
        rawHex: payloadHex,
        payloadLength
      };
      
      // Cellular UC300 specific decoding
      // Based on typical cellular device payload structure
      
      // Extract IMEI (usually first 15 bytes)
      if (payloadLength >= 15) {
        const imeiBytes = payload.slice(0, 15);
        decoded.imei = imeiBytes.toString('ascii');
      }
      
      // Extract signal strength (usually byte 16)
      if (payloadLength >= 16) {
        decoded.signalStrength = payload.readUInt8(15);
      }
      
      // Extract network type (usually byte 17)
      if (payloadLength >= 17) {
        const networkByte = payload.readUInt8(16);
        decoded.networkType = this.getNetworkType(networkByte);
      }
      
      // Extract counters (4 bytes each, starting from byte 18)
      if (payloadLength >= 34) { // 18 + 4*4 = 34
        decoded.counters = [];
        for (let i = 0; i < 4; i++) {
          const offset = 18 + (i * 4);
          const counter = payload.readUInt32LE(offset);
          decoded.counters.push(counter);
        }
      }
      
      // Extract analog inputs (4 bytes each, starting from byte 34)
      if (payloadLength >= 66) { // 34 + 8*4 = 66
        decoded.analogInputs = [];
        for (let i = 0; i < 8; i++) {
          const offset = 34 + (i * 4);
          const rawValue = payload.readUInt32LE(offset);
          const voltage = this.convertToVoltage(rawValue);
          decoded.analogInputs.push(voltage);
        }
      }
      
      // Extract digital inputs (2 bytes, starting from byte 66)
      if (payloadLength >= 68) {
        const dinByte = payload.readUInt16LE(66);
        decoded.digitalInputs = this.byteToBits(dinByte);
      }
      
      // Extract digital outputs (2 bytes, starting from byte 68)
      if (payloadLength >= 70) {
        const doutByte = payload.readUInt16LE(68);
        decoded.digitalOutputs = this.byteToBits(doutByte);
      }
      
      return decoded;
      
    } catch (error) {
      console.error('Error decoding UC300 Cellular payload:', error);
      return null;
    }
  }
  
  /**
   * Convert raw analog value to voltage
   */
  private static convertToVoltage(rawValue: number): number {
    // UC300 Cellular typically uses 0-10V or 4-20mA
    // Convert 32-bit raw value to voltage
    const voltage = (rawValue / 0xFFFFFFFF) * 10.0;
    return Math.round(voltage * 100) / 100;
  }
  
  /**
   * Convert byte to array of bits
   */
  private static byteToBits(value: number): boolean[] {
    const bits: boolean[] = [];
    for (let i = 0; i < 16; i++) {
      bits.push((value & (1 << i)) !== 0);
    }
    return bits;
  }
  
  /**
   * Get network type from byte
   */
  private static getNetworkType(byte: number): string {
    switch (byte) {
      case 0x01: return 'GSM';
      case 0x02: return 'GPRS';
      case 0x03: return 'EDGE';
      case 0x04: return '3G';
      case 0x05: return '4G';
      case 0x06: return '5G';
      default: return 'Unknown';
    }
  }
  
  /**
   * Get human readable status
   */
  static getReadableStatus(payload: UC300CellularPayload) {
    return {
      deviceId: payload.deviceId,
      timestamp: payload.timestamp,
      messageType: payload.messageType,
      cellular: {
        signalStrength: payload.signalStrength ? `${payload.signalStrength}/31` : 'N/A',
        networkType: payload.networkType || 'N/A',
        imei: payload.imei || 'N/A'
      },
      data: {
        counters: payload.counters || [],
        analogInputs: payload.analogInputs || [],
        digitalInputs: payload.digitalInputs || [],
        digitalOutputs: payload.digitalOutputs || []
      }
    };
  }
  
  /**
   * Validate payload for cellular format
   */
  static validateCellularPayload(payload: UC300CellularPayload): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    if (!payload.deviceId) {
      errors.push('Missing device ID');
    }
    
    if (payload.signalStrength && (payload.signalStrength < 0 || payload.signalStrength > 31)) {
      errors.push('Invalid signal strength');
    }
    
    if (payload.counters && payload.counters.some(c => c < 0)) {
      errors.push('Invalid counter values');
    }
    
    if (payload.analogInputs && payload.analogInputs.some(v => v < 0 || v > 10)) {
      errors.push('Invalid analog values');
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
} 