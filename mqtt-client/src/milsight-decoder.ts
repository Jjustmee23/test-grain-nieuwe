// Milsight UC300 Cellular Device Payload Decoder
// Based on the RawData schema from the database

export interface MilsightPayload {
  startFlag: number;
  dataType: number;
  length: number;
  version: number;
  deviceId: string;
  
  // Digital Inputs/Outputs
  doutEnabled: string;
  dout: string;
  diMode: string;
  din: string;
  
  // Counters
  counter1: number;
  counter2: number;
  counter3: number;
  counter4: number;
  
  // Analog Inputs
  ainMode: string;
  ain1Value: number;
  ain2Value: number;
  ain3Value: number;
  ain4Value: number;
  ain5Value: number;
  ain6Value: number;
  ain7Value: number;
  ain8Value: number;
  
  // Cellular
  mobileSignal: number;
  
  endFlag: number;
  timestamp: Date;
}

export class MilsightDecoder {
  
  /**
   * Decode hex payload from UC300 device
   * @param hexPayload - Raw hex string from MQTT
   * @returns Decoded Milsight payload
   */
  static decodeHexPayload(hexPayload: string): MilsightPayload | null {
    try {
      console.log(`🔍 Decoding hex payload: ${hexPayload}`);
      
      // Remove any whitespace or prefixes
      const cleanHex = hexPayload.replace(/\s/g, '').toLowerCase();
      
      // Convert hex to buffer
      const buffer = Buffer.from(cleanHex, 'hex');
      
      if (buffer.length < 20) {
        console.error('❌ Payload too short for valid Milsight data');
        return null;
      }
      
      let offset = 0;
      
      // Read header fields
      const startFlag = buffer.readUInt8(offset++);
      const dataType = buffer.readUInt8(offset++);
      const length = buffer.readUInt16LE(offset); offset += 2;
      const version = buffer.readUInt8(offset++);
      
      // Read device ID (6 bytes)
      const deviceIdBytes = buffer.slice(offset, offset + 6);
      const deviceId = deviceIdBytes.toString('hex').toUpperCase();
      offset += 6;
      
      // Read digital outputs (2 bytes)
      const doutEnabled = buffer.readUInt16LE(offset).toString(2).padStart(16, '0');
      offset += 2;
      const dout = buffer.readUInt16LE(offset).toString(2).padStart(16, '0');
      offset += 2;
      
      // Read digital inputs (2 bytes)
      const diMode = buffer.readUInt16LE(offset).toString(2).padStart(16, '0');
      offset += 2;
      const din = buffer.readUInt16LE(offset).toString(2).padStart(16, '0');
      offset += 2;
      
      // Read counters (4 x 4 bytes = 16 bytes)
      const counter1 = buffer.readUInt32LE(offset); offset += 4;
      const counter2 = buffer.readUInt32LE(offset); offset += 4;
      const counter3 = buffer.readUInt32LE(offset); offset += 4;
      const counter4 = buffer.readUInt32LE(offset); offset += 4;
      
      // Read analog input mode (2 bytes)
      const ainMode = buffer.readUInt16LE(offset).toString(2).padStart(16, '0');
      offset += 2;
      
      // Read analog inputs (8 x 4 bytes = 32 bytes)
      const ain1Value = this.convertAnalogValue(buffer.readUInt32LE(offset)); offset += 4;
      const ain2Value = this.convertAnalogValue(buffer.readUInt32LE(offset)); offset += 4;
      const ain3Value = this.convertAnalogValue(buffer.readUInt32LE(offset)); offset += 4;
      const ain4Value = this.convertAnalogValue(buffer.readUInt32LE(offset)); offset += 4;
      const ain5Value = this.convertAnalogValue(buffer.readUInt32LE(offset)); offset += 4;
      const ain6Value = this.convertAnalogValue(buffer.readUInt32LE(offset)); offset += 4;
      const ain7Value = this.convertAnalogValue(buffer.readUInt32LE(offset)); offset += 4;
      const ain8Value = this.convertAnalogValue(buffer.readUInt32LE(offset)); offset += 4;
      
      // Read mobile signal strength (1 byte)
      const mobileSignal = buffer.readUInt8(offset++);
      
      // Read end flag
      const endFlag = buffer.readUInt8(offset);
      
      const decoded: MilsightPayload = {
        startFlag,
        dataType,
        length,
        version,
        deviceId,
        doutEnabled,
        dout,
        diMode,
        din,
        counter1,
        counter2,
        counter3,
        counter4,
        ainMode,
        ain1Value,
        ain2Value,
        ain3Value,
        ain4Value,
        ain5Value,
        ain6Value,
        ain7Value,
        ain8Value,
        mobileSignal,
        endFlag,
        timestamp: new Date()
      };
      
      console.log('✅ Successfully decoded Milsight payload:', decoded);
      return decoded;
      
    } catch (error) {
      console.error('❌ Error decoding Milsight payload:', error);
      return null;
    }
  }
  
  /**
   * Convert raw analog value to voltage/temperature
   * @param rawValue - Raw 32-bit analog value
   * @returns Converted value
   */
  private static convertAnalogValue(rawValue: number): number {
    // UC300 typically uses 0-10V or 4-20mA inputs
    // Convert to voltage (0-10V range)
    const voltage = (rawValue / 0xFFFFFFFF) * 10.0;
    return Math.round(voltage * 100) / 100; // Round to 2 decimal places
  }
  
  /**
   * Parse digital input/output states
   * @param binaryString - Binary string representation
   * @returns Array of boolean states
   */
  static parseDigitalStates(binaryString: string): boolean[] {
    return binaryString.split('').map(bit => bit === '1');
  }
  
  /**
   * Get human readable status
   * @param payload - Decoded payload
   * @returns Human readable status object
   */
  static getReadableStatus(payload: MilsightPayload) {
    const dinStates = this.parseDigitalStates(payload.din);
    const doutStates = this.parseDigitalStates(payload.dout);
    
    return {
      deviceId: payload.deviceId,
      timestamp: payload.timestamp,
      mobileSignal: `${payload.mobileSignal}/31`,
      digitalInputs: {
        input1: dinStates[0] || false,
        input2: dinStates[1] || false,
        input3: dinStates[2] || false,
        input4: dinStates[3] || false,
        input5: dinStates[4] || false,
        input6: dinStates[5] || false,
        input7: dinStates[6] || false,
        input8: dinStates[7] || false,
      },
      digitalOutputs: {
        output1: doutStates[0] || false,
        output2: doutStates[1] || false,
        output3: doutStates[2] || false,
        output4: doutStates[3] || false,
        output5: doutStates[4] || false,
        output6: doutStates[5] || false,
        output7: doutStates[6] || false,
        output8: doutStates[7] || false,
      },
      counters: {
        counter1: payload.counter1,
        counter2: payload.counter2,
        counter3: payload.counter3,
        counter4: payload.counter4,
      },
      analogInputs: {
        ain1: `${payload.ain1Value}V`,
        ain2: `${payload.ain2Value}V`,
        ain3: `${payload.ain3Value}V`,
        ain4: `${payload.ain4Value}V`,
        ain5: `${payload.ain5Value}V`,
        ain6: `${payload.ain6Value}V`,
        ain7: `${payload.ain7Value}V`,
        ain8: `${payload.ain8Value}V`,
      }
    };
  }
  
  /**
   * Validate payload structure
   * @param payload - Decoded payload
   * @returns Validation result
   */
  static validatePayload(payload: MilsightPayload): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    if (payload.startFlag !== 0xAA) {
      errors.push('Invalid start flag');
    }
    
    if (payload.endFlag !== 0x55) {
      errors.push('Invalid end flag');
    }
    
    if (payload.deviceId.length !== 12) {
      errors.push('Invalid device ID length');
    }
    
    if (payload.mobileSignal > 31) {
      errors.push('Invalid mobile signal strength');
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
} 