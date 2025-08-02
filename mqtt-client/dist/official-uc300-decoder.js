"use strict";
// Official UC300 Decoder based on Milesight Documentation
// Supports F2 (Change Report), F3 (Attribute Report), F4 (Regular Report)
Object.defineProperty(exports, "__esModule", { value: true });
exports.OfficialUC300Decoder = void 0;
class OfficialUC300Decoder {
    /**
     * Decode UC300 payload according to official Milesight protocol
     */
    static decodePayload(buffer) {
        try {
            if (buffer.length < 5) {
                console.error('❌ Payload too short');
                return null;
            }
            let offset = 0;
            // Start Flag
            const startFlag = buffer.readUInt8(offset++);
            if (startFlag !== 0x7E) {
                console.error('❌ Invalid start flag:', startFlag);
                return null;
            }
            // Data Type
            const dataType = buffer.readUInt8(offset++);
            // Packet Length (2 bytes, little endian)
            const packetLength = buffer.readUInt16LE(offset);
            offset += 2;
            // Data Section
            let data = null;
            switch (dataType) {
                case 0xF2:
                    data = this.decodeChangeReport(buffer, offset);
                    break;
                case 0xF3:
                    data = this.decodeAttributeReport(buffer, offset);
                    break;
                case 0xF4:
                    data = this.decodeRegularReport(buffer, offset);
                    break;
                default:
                    console.warn(`⚠️ Unknown data type: 0x${dataType.toString(16).toUpperCase()}`);
                    data = { raw: buffer.slice(offset, buffer.length - 1).toString('hex') };
            }
            // End Flag
            const endFlag = buffer.readUInt8(buffer.length - 1);
            if (endFlag !== 0x7E) {
                console.error('❌ Invalid end flag:', endFlag);
                return null;
            }
            return {
                startFlag,
                dataType,
                packetLength,
                endFlag,
                data
            };
        }
        catch (error) {
            console.error('❌ Error decoding UC300 payload:', error);
            return null;
        }
    }
    /**
     * Decode F2: Change Report
     */
    static decodeChangeReport(buffer, offset) {
        try {
            // Packet Version
            const version = buffer.readUInt8(offset++);
            // Timestamp (4 bytes, little endian)
            const timestamp = buffer.readUInt32LE(offset);
            offset += 4;
            // Toggles of Digital Inputs (1 byte)
            const diToggles = buffer.readUInt8(offset++);
            // Parse DI modes (2 bits each)
            const diModes = [
                diToggles & 0x03, // DI1: bits 0-1
                (diToggles >> 2) & 0x03, // DI2: bits 2-3
                (diToggles >> 4) & 0x03, // DI3: bits 4-5
                (diToggles >> 6) & 0x03 // DI4: bits 6-7
            ];
            // Digital Input Status (if any in Digital Input mode)
            let diStatus = [];
            const hasDigitalInputs = diModes.some(mode => mode === 1);
            if (hasDigitalInputs) {
                const diStatusByte = buffer.readUInt8(offset++);
                diStatus = [
                    (diStatusByte & 0x01) !== 0, // DI1
                    (diStatusByte & 0x02) !== 0, // DI2
                    (diStatusByte & 0x04) !== 0, // DI3
                    (diStatusByte & 0x08) !== 0 // DI4
                ];
            }
            // Counter Values (if any in Counter mode)
            const counterValues = [];
            diModes.forEach((mode, index) => {
                if (mode === 2 || mode === 3) { // Counter mode
                    const counterValue = buffer.readUInt32LE(offset);
                    offset += 4;
                    counterValues[index] = counterValue;
                }
                else {
                    counterValues[index] = 0;
                }
            });
            // Toggles of Digital Outputs
            const doutToggles = buffer.readUInt8(offset++);
            const doutEnabled = [
                (doutToggles & 0x01) !== 0, // DO1
                (doutToggles & 0x02) !== 0 // DO2
            ];
            // Digital Output Status (if any enabled)
            let doutStatus = [];
            if (doutToggles !== 0x00) {
                const doutByte = buffer.readUInt8(offset++);
                doutStatus = [
                    (doutByte & 0x01) !== 0, // DO1
                    (doutByte & 0x02) !== 0 // DO2
                ];
            }
            return {
                version,
                timestamp,
                diModes,
                diStatus,
                counterValues,
                doutEnabled,
                doutStatus
            };
        }
        catch (error) {
            console.error('❌ Error decoding change report:', error);
            return null;
        }
    }
    /**
     * Decode F3: Attribute Report
     */
    static decodeAttributeReport(buffer, offset) {
        try {
            // Packet Version
            const version = buffer.readUInt8(offset++);
            // UCP Version
            const ucpVersion = buffer.readUInt8(offset++);
            // Serial Number (16 bytes)
            const serialNumber = buffer.toString('ascii', offset, offset + 16);
            offset += 16;
            // Hardware Version (4 bytes)
            const hardwareVersion = buffer.toString('ascii', offset, offset + 4);
            offset += 4;
            // Firmware Version (4 bytes)
            const firmwareVersion = buffer.toString('ascii', offset, offset + 4);
            offset += 4;
            // IMEI (15 bytes)
            const imei = buffer.toString('ascii', offset, offset + 15);
            offset += 15;
            // IMSI (15 bytes)
            const imsi = buffer.toString('ascii', offset, offset + 15);
            offset += 15;
            // ICCID (20 bytes)
            const iccid = buffer.toString('ascii', offset, offset + 20);
            return {
                version,
                ucpVersion: `V${ucpVersion}`,
                serialNumber,
                hardwareVersion,
                firmwareVersion,
                imei,
                imsi,
                iccid
            };
        }
        catch (error) {
            console.error('❌ Error decoding attribute report:', error);
            return null;
        }
    }
    /**
     * Decode F4: Regular Report
     */
    static decodeRegularReport(buffer, offset) {
        try {
            // Packet Version
            const version = buffer.readUInt8(offset++);
            // Timestamp (4 bytes, little endian)
            const timestamp = buffer.readUInt32LE(offset);
            offset += 4;
            // Signal Strength
            const signalStrength = buffer.readUInt8(offset++);
            // Toggles of Digital Outputs
            const doutToggles = buffer.readUInt8(offset++);
            const doutEnabled = [
                (doutToggles & 0x01) !== 0, // DO1
                (doutToggles & 0x02) !== 0 // DO2
            ];
            // Digital Output Status (if any enabled)
            let doutStatus = [];
            if (doutToggles !== 0x00) {
                const doutByte = buffer.readUInt8(offset++);
                doutStatus = [
                    (doutByte & 0x01) !== 0, // DO1
                    (doutByte & 0x02) !== 0 // DO2
                ];
            }
            // Toggles of Digital Inputs (1 byte)
            const diToggles = buffer.readUInt8(offset++);
            // Parse DI modes (2 bits each)
            const diModes = [
                diToggles & 0x03, // DI1: bits 0-1
                (diToggles >> 2) & 0x03, // DI2: bits 2-3
                (diToggles >> 4) & 0x03, // DI3: bits 4-5
                (diToggles >> 6) & 0x03 // DI4: bits 6-7
            ];
            // Digital Input Status (if any in Digital Input mode)
            let diStatus = [];
            const hasDigitalInputs = diModes.some(mode => mode === 1);
            if (hasDigitalInputs) {
                const diStatusByte = buffer.readUInt8(offset++);
                diStatus = [
                    (diStatusByte & 0x01) !== 0, // DI1
                    (diStatusByte & 0x02) !== 0, // DI2
                    (diStatusByte & 0x04) !== 0, // DI3
                    (diStatusByte & 0x08) !== 0 // DI4
                ];
            }
            // Counter Values (if any in Counter mode)
            const counterValues = [];
            diModes.forEach((mode, index) => {
                if (mode === 2 || mode === 3) { // Counter mode
                    const counterValue = buffer.readUInt32LE(offset);
                    offset += 4;
                    counterValues[index] = counterValue;
                }
                else {
                    counterValues[index] = 0;
                }
            });
            // Toggles of Analog Inputs (2 bytes)
            const ainToggles = buffer.readUInt16LE(offset);
            offset += 2;
            // Parse AI modes (2 bits each for 8 inputs)
            const ainModes = [];
            for (let i = 0; i < 8; i++) {
                ainModes[i] = (ainToggles >> (i * 2)) & 0x03;
            }
            // Analog Input Values (if any enabled)
            const ainValues = [];
            ainModes.forEach((mode, index) => {
                if (mode === 1) { // Successfully collected
                    const value = buffer.readFloatLE(offset);
                    offset += 4;
                    ainValues[index] = value;
                }
                else {
                    ainValues[index] = 0;
                }
            });
            // Modbus Data (if any)
            const modbusData = [];
            while (offset < buffer.length - 1) { // -1 for end flag
                if (offset + 2 > buffer.length - 1)
                    break;
                const mode1 = buffer.readUInt8(offset++);
                const mode2 = buffer.readUInt8(offset++);
                // Parse modbus channel
                const channelId = mode1 >> 3;
                const dataType = mode1 & 0x07;
                const sign = (mode2 >> 7) & 0x01;
                const collectSuccess = (mode2 >> 3) & 0x01;
                const quantity = mode2 & 0x07;
                if (collectSuccess && quantity > 0) {
                    const values = [];
                    for (let i = 0; i < quantity; i++) {
                        let value;
                        switch (dataType) {
                            case 0: // Coil
                            case 1: // Discrete
                                value = buffer.readUInt8(offset++);
                                break;
                            case 2: // Input16
                            case 3: // Hold16
                                value = sign ? buffer.readInt16LE(offset) : buffer.readUInt16LE(offset);
                                offset += 2;
                                break;
                            case 4: // Hold32
                            case 6: // Input32
                                value = sign ? buffer.readInt32LE(offset) : buffer.readUInt32LE(offset);
                                offset += 4;
                                break;
                            case 5: // Hold_float
                            case 7: // Input_float
                                value = buffer.readFloatLE(offset);
                                offset += 4;
                                break;
                            default:
                                value = buffer.readUInt16LE(offset);
                                offset += 2;
                        }
                        values.push(value);
                    }
                    modbusData.push({
                        channelId: channelId + 1,
                        dataType,
                        sign,
                        quantity,
                        values
                    });
                }
            }
            return {
                version,
                timestamp,
                signalStrength,
                doutEnabled,
                doutStatus,
                diModes,
                diStatus,
                counterValues,
                ainModes,
                ainValues,
                modbusData: modbusData.length > 0 ? modbusData : undefined
            };
        }
        catch (error) {
            console.error('❌ Error decoding regular report:', error);
            return null;
        }
    }
    /**
     * Get human readable status
     */
    static getReadableStatus(payload) {
        const dataTypeNames = {
            0xF2: 'Change Report',
            0xF3: 'Attribute Report',
            0xF4: 'Regular Report'
        };
        const diModeNames = ['Disabled', 'Digital Input', 'Counter-Stop', 'Counter-Start'];
        const aiModeNames = ['Disabled', 'Success', 'Failed', 'Reserved'];
        const result = {
            dataType: dataTypeNames[payload.dataType] || `Unknown (0x${payload.dataType.toString(16).toUpperCase()})`,
            packetLength: payload.packetLength
        };
        if (payload.dataType === 0xF2) {
            const changeData = payload.data;
            result.timestamp = new Date(changeData.timestamp * 1000);
            result.digitalInputs = changeData.diModes.map((mode, index) => ({
                [`DI${index + 1}`]: {
                    mode: diModeNames[mode],
                    status: mode === 1 ? (changeData.diStatus[index] ? 'High' : 'Low') : 'N/A',
                    counter: (mode === 2 || mode === 3) ? changeData.counterValues[index] : 'N/A'
                }
            }));
            result.digitalOutputs = changeData.doutEnabled.map((enabled, index) => ({
                [`DO${index + 1}`]: {
                    enabled,
                    status: enabled ? (changeData.doutStatus[index] ? 'Open' : 'Closed') : 'Disabled'
                }
            }));
        }
        if (payload.dataType === 0xF3) {
            const attrData = payload.data;
            result.deviceInfo = {
                serialNumber: attrData.serialNumber,
                hardwareVersion: attrData.hardwareVersion,
                firmwareVersion: attrData.firmwareVersion,
                imei: attrData.imei,
                imsi: attrData.imsi,
                iccid: attrData.iccid
            };
        }
        if (payload.dataType === 0xF4) {
            const regularData = payload.data;
            result.timestamp = new Date(regularData.timestamp * 1000);
            result.signalStrength = `${regularData.signalStrength} asu (${-113 + 2 * regularData.signalStrength} dBm)`;
            result.digitalInputs = regularData.diModes.map((mode, index) => ({
                [`DI${index + 1}`]: {
                    mode: diModeNames[mode],
                    status: mode === 1 ? (regularData.diStatus[index] ? 'High' : 'Low') : 'N/A',
                    counter: (mode === 2 || mode === 3) ? regularData.counterValues[index] : 'N/A'
                }
            }));
            result.digitalOutputs = regularData.doutEnabled.map((enabled, index) => ({
                [`DO${index + 1}`]: {
                    enabled,
                    status: enabled ? (regularData.doutStatus[index] ? 'Open' : 'Closed') : 'Disabled'
                }
            }));
            result.analogInputs = regularData.ainModes.map((mode, index) => ({
                [`AI${index + 1}`]: {
                    mode: aiModeNames[mode],
                    value: mode === 1 ? `${regularData.ainValues[index]} mA/V` : 'N/A'
                }
            }));
            if (regularData.modbusData) {
                result.modbusData = regularData.modbusData;
            }
        }
        return result;
    }
}
exports.OfficialUC300Decoder = OfficialUC300Decoder;
//# sourceMappingURL=official-uc300-decoder.js.map