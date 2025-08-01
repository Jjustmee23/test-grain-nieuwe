"use strict";
// UC300 Device Decoder
// Based on the actual data format we received from the broker
Object.defineProperty(exports, "__esModule", { value: true });
exports.UC300Decoder = void 0;
class UC300Decoder {
    /**
     * Decode UC300 status payload
     * @param deviceId - Device ID from topic
     * @param payload - Raw buffer payload
     * @returns Decoded UC300 payload
     */
    static decodeStatusPayload(deviceId, payload) {
        try {
            console.log(`🔍 Decoding UC300 payload for device: ${deviceId}`);
            console.log(`📦 Raw payload (hex): ${payload.toString('hex')}`);
            console.log(`📦 Raw payload (length): ${payload.length} bytes`);
            // The payload seems to be binary data, not hex string
            // Let's analyze the structure
            const decoded = {
                deviceId,
                timestamp: new Date(),
                status: 'unknown',
                rawData: payload
            };
            // Try to extract meaningful data
            if (payload.length >= 8) {
                // Look for patterns in the data
                const header = payload.slice(0, 4);
                const data = payload.slice(4);
                console.log(`📋 Header (hex): ${header.toString('hex')}`);
                console.log(`📋 Data (hex): ${data.toString('hex')}`);
                // Try to find device ID in the payload
                const deviceIdInPayload = this.findDeviceIdInPayload(payload, deviceId);
                if (deviceIdInPayload) {
                    console.log(`✅ Found device ID in payload: ${deviceIdInPayload}`);
                }
                // Try to extract counter values
                const counters = this.extractCounters(payload);
                if (counters.length > 0) {
                    decoded.decodedData = { counters };
                    console.log(`🔢 Extracted counters:`, counters);
                }
                // Try to extract analog values
                const analogs = this.extractAnalogValues(payload);
                if (analogs.length > 0) {
                    if (!decoded.decodedData)
                        decoded.decodedData = {};
                    decoded.decodedData.analogs = analogs;
                    console.log(`📊 Extracted analog values:`, analogs);
                }
                // Try to extract digital states
                const digitals = this.extractDigitalStates(payload);
                if (digitals.length > 0) {
                    if (!decoded.decodedData)
                        decoded.decodedData = {};
                    decoded.decodedData.digitals = digitals;
                    console.log(`🔌 Extracted digital states:`, digitals);
                }
            }
            console.log('✅ Successfully decoded UC300 payload');
            return decoded;
        }
        catch (error) {
            console.error('❌ Error decoding UC300 payload:', error);
            return null;
        }
    }
    /**
     * Find device ID in payload
     */
    static findDeviceIdInPayload(payload, expectedDeviceId) {
        const payloadHex = payload.toString('hex').toUpperCase();
        const deviceIdHex = expectedDeviceId.replace(/[^0-9A-F]/g, '');
        if (payloadHex.includes(deviceIdHex)) {
            return expectedDeviceId;
        }
        return null;
    }
    /**
     * Extract counter values from payload
     */
    static extractCounters(payload) {
        const counters = [];
        // Look for 4-byte sequences that could be counters
        for (let i = 0; i <= payload.length - 4; i++) {
            const value = payload.readUInt32LE(i);
            // Filter out unlikely counter values (too large or zero)
            if (value > 0 && value < 1000000000) {
                counters.push(value);
            }
        }
        return counters.slice(0, 4); // Return max 4 counters
    }
    /**
     * Extract analog values from payload
     */
    static extractAnalogValues(payload) {
        const analogs = [];
        // Look for 4-byte sequences that could be analog values
        for (let i = 0; i <= payload.length - 4; i++) {
            const rawValue = payload.readUInt32LE(i);
            // Convert to voltage (0-10V range)
            const voltage = (rawValue / 0xFFFFFFFF) * 10.0;
            if (voltage >= 0 && voltage <= 10) {
                analogs.push(Math.round(voltage * 100) / 100);
            }
        }
        return analogs.slice(0, 8); // Return max 8 analog inputs
    }
    /**
     * Extract digital states from payload
     */
    static extractDigitalStates(payload) {
        const states = [];
        // Look for byte values that could represent digital states
        for (let i = 0; i < payload.length; i++) {
            const byte = payload.readUInt8(i);
            // Check if byte could represent digital states (0x00, 0x01, 0xFF, etc.)
            if (byte === 0x00 || byte === 0x01 || byte === 0xFF ||
                byte === 0x0F || byte === 0xF0 || byte === 0xAA || byte === 0x55) {
                // Convert byte to 8 boolean states
                for (let bit = 0; bit < 8; bit++) {
                    states.push((byte & (1 << bit)) !== 0);
                }
            }
        }
        return states.slice(0, 16); // Return max 16 digital states
    }
    /**
     * Get human readable status
     */
    static getReadableStatus(payload) {
        return {
            deviceId: payload.deviceId,
            timestamp: payload.timestamp,
            status: payload.status,
            hasDecodedData: !!payload.decodedData,
            decodedData: payload.decodedData
        };
    }
    /**
     * Analyze payload structure
     */
    static analyzePayload(payload) {
        const analysis = {
            length: payload.length,
            hex: payload.toString('hex'),
            ascii: payload.toString('ascii'),
            utf8: payload.toString('utf8'),
            bytes: Array.from(payload),
            patterns: {
                zeros: 0,
                ones: 0,
                repeating: 0
            }
        };
        // Count patterns
        for (let i = 0; i < payload.length; i++) {
            const byte = payload.readUInt8(i);
            if (byte === 0)
                analysis.patterns.zeros++;
            if (byte === 1)
                analysis.patterns.ones++;
            if (i > 0 && byte === payload.readUInt8(i - 1))
                analysis.patterns.repeating++;
        }
        return analysis;
    }
}
exports.UC300Decoder = UC300Decoder;
//# sourceMappingURL=uc300-decoder.js.map