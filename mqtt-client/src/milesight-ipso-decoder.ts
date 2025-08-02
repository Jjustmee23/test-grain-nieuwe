// Milesight UC300 IPSO Protocol Decoder
// Based on official Milesight protocol documentation

export interface MilesightIPSOData {
  deviceId: string;
  timestamp: Date;
  fPort: number;
  uplinkType: 'attribute-report' | 'regular-report';
  
  // Device Information (FF channels)
  protocolVersion?: string;
  hardwareVersion?: string;
  firmwareVersion?: string;
  powerOnTime?: number;
  serialNumber?: string;
  
  // Sensor Data
  digitalInputs: boolean[];
  digitalOutputs: boolean[];
  analogInputs: { [key: string]: number };
  pt100Temperatures: { [key: string]: number };
  modbusData?: any;
  
  // Raw data for debugging
  rawPayload: Buffer;
  decodedChannels: { [channel: string]: any };
}

export class MilesightIPSODecoder {
  
  /**
   * Decode Milesight IPSO payload
   * @param deviceId - Device ID from topic
   * @param payload - Raw buffer payload
   * @param fPort - fPort number (should be 85 for UC300)
   * @returns Decoded IPSO data
   */
  static decodeIPSO(deviceId: string, payload: Buffer, fPort: number = 85): MilesightIPSOData | null {
    try {
      console.log(`🔍 Decoding Milesight IPSO payload for device: ${deviceId}`);
      console.log(`📦 fPort: ${fPort}, Payload length: ${payload.length} bytes`);
      
      const decoded: MilesightIPSOData = {
        deviceId,
        timestamp: new Date(),
        fPort,
        uplinkType: 'regular-report',
        digitalInputs: [],
        digitalOutputs: [],
        analogInputs: {},
        pt100Temperatures: {},
        rawPayload: payload,
        decodedChannels: {}
      };
      
      let offset = 0;
      
      // Parse channels
      while (offset < payload.length) {
        const channel = payload.readUInt8(offset++);
        const dataType = payload.readUInt8(offset++);
        const dataLength = payload.readUInt8(offset++);
        
        console.log(`📋 Channel: 0x${channel.toString(16).toUpperCase()}, Type: 0x${dataType.toString(16).toUpperCase()}, Length: ${dataLength}`);
        
        if (offset + dataLength > payload.length) {
          console.error('❌ Payload too short for channel data');
          break;
        }
        
        const channelData = payload.slice(offset, offset + dataLength);
        const decodedChannel = this.decodeChannel(channel, dataType, channelData);
        
        if (decodedChannel) {
          decoded.decodedChannels[`0x${channel.toString(16).toUpperCase()}`] = decodedChannel;
          
          // Store in appropriate arrays/objects
          this.storeChannelData(decoded, channel, decodedChannel);
        }
        
        offset += dataLength;
      }
      
      console.log('✅ Successfully decoded Milesight IPSO payload');
      return decoded;
      
    } catch (error) {
      console.error('❌ Error decoding Milesight IPSO payload:', error);
      return null;
    }
  }
  
  /**
   * Decode individual channel
   */
  private static decodeChannel(channel: number, dataType: number, data: Buffer): any {
    try {
      switch (channel) {
        // Device Information (FF channels)
        case 0xFF:
          return this.decodeFFChannel(dataType, data);
          
        // Digital Inputs (03-06)
        case 0x03:
        case 0x04:
        case 0x05:
        case 0x06:
          return this.decodeDigitalInput(channel, dataType, data);
          
        // Digital Outputs (07-08)
        case 0x07:
        case 0x08:
          return this.decodeDigitalOutput(channel, dataType, data);
          
        // PT100 Temperature (09-0A)
        case 0x09:
        case 0x0A:
          return this.decodePT100(channel, dataType, data);
          
        // Analog Inputs 4-20mA / 0-10V (0B-0E)
        case 0x0B:
        case 0x0C:
        case 0x0D:
        case 0x0E:
          return this.decodeAnalogInput(channel, dataType, data);
          
        // Modbus Data (FF 19)
        case 0x19:
          return this.decodeModbusData(dataType, data);
          
        default:
          console.log(`⚠️ Unknown channel: 0x${channel.toString(16).toUpperCase()}`);
          return { raw: data.toString('hex').toUpperCase() };
      }
    } catch (error: any) { // Explicitly type error as 'any' or 'Error'
      console.error(`Error decoding channel 0x${channel.toString(16).toUpperCase()}:`, error);
      return { error: error.message, raw: data.toString('hex').toUpperCase() };
    }
  }
  
  /**
   * Decode FF channels (device information)
   */
  private static decodeFFChannel(dataType: number, data: Buffer): any {
    switch (dataType) {
      case 0x01: // Protocol version
        return { type: 'protocol-version', value: data.toString('ascii') };
      case 0x09: // Hardware version
        return { type: 'hardware-version', value: data.toString('ascii') };
      case 0x0A: // Firmware version
        return { type: 'firmware-version', value: data.toString('ascii') };
      case 0x0B: // Power-on time
        return { type: 'power-on-time', value: data.readUInt32LE(0) };
      case 0x16: // Serial number (8 bytes)
        return { type: 'serial-number', value: data.toString('hex').toUpperCase() };
      default:
        return { type: 'unknown-ff', dataType, value: data.toString('hex').toUpperCase() };
    }
  }
  
  /**
   * Decode Digital Input (channels 03-06)
   */
  private static decodeDigitalInput(channel: number, dataType: number, data: Buffer): any {
    const inputNumber = channel - 0x02; // 03->1, 04->2, etc.
    
    if (dataType === 0x00) { // Boolean
      return {
        type: 'digital-input',
        input: inputNumber,
        value: data.readUInt8(0) !== 0,
        counter: data.length > 1 ? data.readUInt32LE(1) : 0
      };
    }
    
    return {
      type: 'digital-input',
      input: inputNumber,
      raw: data.toString('hex').toUpperCase()
    };
  }
  
  /**
   * Decode Digital Output (channels 07-08)
   */
  private static decodeDigitalOutput(channel: number, dataType: number, data: Buffer): any {
    const outputNumber = channel - 0x06; // 07->1, 08->2
    
    if (dataType === 0x00) { // Boolean
      return {
        type: 'digital-output',
        output: outputNumber,
        value: data.readUInt8(0) !== 0
      };
    }
    
    return {
      type: 'digital-output',
      output: outputNumber,
      raw: data.toString('hex').toUpperCase()
    };
  }
  
  /**
   * Decode PT100 Temperature (channels 09-0A)
   */
  private static decodePT100(channel: number, dataType: number, data: Buffer): any {
    const sensorNumber = channel - 0x08; // 09->1, 0A->2
    
    if (dataType === 0x01) { // INT16
      const rawValue = data.readInt16LE(0);
      const temperature = rawValue / 10.0; // INT16/10 → °C
      
      return {
        type: 'pt100-temperature',
        sensor: sensorNumber,
        temperature: temperature.toFixed(1),
        rawValue
      };
    }
    
    return {
      type: 'pt100-temperature',
      sensor: sensorNumber,
      raw: data.toString('hex').toUpperCase()
    };
  }
  
  /**
   * Decode Analog Input (channels 0B-0E)
   */
  private static decodeAnalogInput(channel: number, dataType: number, data: Buffer): any {
    const inputNumber = channel - 0x0A; // 0B->1, 0C->2, etc.
    
    if (dataType === 0x06) { // UINT32
      const rawValue = data.readUInt32LE(0);
      const scaledValue = rawValue / 100.0; // UINT32/100
      
      return {
        type: 'analog-input',
        input: inputNumber,
        value: scaledValue.toFixed(2),
        rawValue,
        unit: 'mA/V'
      };
    } else if (dataType === 0x08) { // Float
      const floatValue = data.readFloatLE(0);
      
      return {
        type: 'analog-input',
        input: inputNumber,
        value: floatValue.toFixed(2),
        rawValue: floatValue,
        unit: 'mA/V'
      };
    }
    
    return {
      type: 'analog-input',
      input: inputNumber,
      raw: data.toString('hex').toUpperCase()
    };
  }
  
  /**
   * Decode Modbus Data (channel FF 19)
   */
  private static decodeModbusData(dataType: number, data: Buffer): any {
    return {
      type: 'modbus-data',
      dataType,
      registers: data.toString('hex').toUpperCase(),
      length: data.length
    };
  }
  
  /**
   * Store decoded channel data in main object
   */
  private static storeChannelData(decoded: MilesightIPSOData, channel: number, channelData: any) {
    switch (channelData.type) {
      case 'digital-input':
        while (decoded.digitalInputs.length < channelData.input) {
          decoded.digitalInputs.push(false);
        }
        decoded.digitalInputs[channelData.input - 1] = channelData.value;
        break;
        
      case 'digital-output':
        while (decoded.digitalOutputs.length < channelData.output) {
          decoded.digitalOutputs.push(false);
        }
        decoded.digitalOutputs[channelData.output - 1] = channelData.value;
        break;
        
      case 'pt100-temperature':
        decoded.pt100Temperatures[`PT100${channelData.sensor}`] = parseFloat(channelData.temperature);
        break;
        
      case 'analog-input':
        decoded.analogInputs[`AIN${channelData.input}`] = parseFloat(channelData.value);
        break;
        
      case 'protocol-version':
        decoded.protocolVersion = channelData.value;
        break;
        
      case 'hardware-version':
        decoded.hardwareVersion = channelData.value;
        break;
        
      case 'firmware-version':
        decoded.firmwareVersion = channelData.value;
        break;
        
      case 'power-on-time':
        decoded.powerOnTime = channelData.value;
        break;
        
      case 'serial-number':
        decoded.serialNumber = channelData.value;
        break;
        
      case 'modbus-data':
        decoded.modbusData = channelData;
        break;
    }
  }
  
  /**
   * Get human readable status
   */
  static getReadableStatus(data: MilesightIPSOData) {
    return {
      deviceId: data.deviceId,
      timestamp: data.timestamp,
      fPort: data.fPort,
      uplinkType: data.uplinkType,
      
      deviceInfo: {
        protocolVersion: data.protocolVersion,
        hardwareVersion: data.hardwareVersion,
        firmwareVersion: data.firmwareVersion,
        powerOnTime: data.powerOnTime,
        serialNumber: data.serialNumber
      },
      
      sensors: {
        digitalInputs: data.digitalInputs.map((state, i) => ({ [`DI${i + 1}`]: state ? 'ON' : 'OFF' })),
        digitalOutputs: data.digitalOutputs.map((state, i) => ({ [`DO${i + 1}`]: state ? 'ON' : 'OFF' })),
        analogInputs: data.analogInputs,
        pt100Temperatures: data.pt100Temperatures
      },
      
      modbus: data.modbusData,
      decodedChannels: data.decodedChannels
    };
  }
} 