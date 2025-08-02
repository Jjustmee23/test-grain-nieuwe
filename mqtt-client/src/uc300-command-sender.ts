// UC300 Command Sender
// Based on official Milesight UC300 protocol

import mqtt, { MqttClient } from 'mqtt';

export interface UC300Command {
  type: 'password' | 'reboot' | 'do-control' | 'query' | 'report-interval' | 'counter-reset';
  data?: any;
}

export class UC300CommandSender {
  private client: MqttClient;
  private deviceId: string;
  private password: string;
  private authenticated: boolean = false;

  constructor(client: MqttClient, deviceId: string, password: string = '123456') {
    this.client = client;
    this.deviceId = deviceId;
    this.password = password;
  }

  /**
   * Send password validation (required before other commands)
   */
  async sendPasswordValidation(): Promise<boolean> {
    const command = this.buildPasswordCommand();
    const topic = `uc/${this.deviceId}/ucp/14/cmd/update`;
    
    return new Promise((resolve) => {
      // Subscribe to reply topic
      const replyTopic = `uc/${this.deviceId}/ucp/14/cmd/update/accepted`;
      this.client.subscribe(replyTopic, (err: any) => {
        if (err) {
          console.error('❌ Failed to subscribe to reply topic:', err);
          resolve(false);
          return;
        }

        // Set up one-time message handler
        const messageHandler = (topic: string, payload: Buffer) => {
          if (topic === replyTopic) {
            this.client.unsubscribe(replyTopic);
            this.client.removeListener('message', messageHandler);
            
            const response = this.parseCommandResponse(payload);
            if (response && response.result === 0x00) {
              console.log('✅ Password validation successful');
              this.authenticated = true;
              resolve(true);
            } else {
              console.log('❌ Password validation failed');
              resolve(false);
            }
          }
        };

        this.client.on('message', messageHandler);

        // Send command
        console.log(`🔐 Sending password validation to ${topic}`);
        this.client.publish(topic, command, (err: any) => {
          if (err) {
            console.error('❌ Failed to send password command:', err);
            resolve(false);
          }
        });

        // Timeout after 10 seconds
        setTimeout(() => {
          this.client.unsubscribe(replyTopic);
          this.client.removeListener('message', messageHandler);
          console.log('⏰ Password validation timeout');
          resolve(false);
        }, 10000);
      });
    });
  }

  /**
   * Control Digital Output
   */
  async controlDigitalOutput(output: 1 | 2, state: 'open' | 'close', duration?: number): Promise<boolean> {
    if (!this.authenticated) {
      console.error('❌ Not authenticated. Send password validation first.');
      return false;
    }

    const command = this.buildDOControlCommand(output, state, duration);
    const topic = `uc/${this.deviceId}/ucp/14/cmd/update`;
    
    return new Promise((resolve) => {
      const replyTopic = `uc/${this.deviceId}/ucp/14/cmd/update/accepted`;
      this.client.subscribe(replyTopic, (err: any) => {
        if (err) {
          console.error('❌ Failed to subscribe to reply topic:', err);
          resolve(false);
          return;
        }

        const messageHandler = (topic: string, payload: Buffer) => {
          if (topic === replyTopic) {
            this.client.unsubscribe(replyTopic);
            this.client.removeListener('message', messageHandler);
            
            const response = this.parseCommandResponse(payload);
            if (response && response.result === 0x00) {
              console.log(`✅ DO${output} ${state} command successful`);
              resolve(true);
            } else {
              console.log(`❌ DO${output} ${state} command failed`);
              resolve(false);
            }
          }
        };

        this.client.on('message', messageHandler);

        console.log(`🔌 Sending DO${output} ${state} command to ${topic}`);
        this.client.publish(topic, command, (err: any) => {
          if (err) {
            console.error('❌ Failed to send DO command:', err);
            resolve(false);
          }
        });

        setTimeout(() => {
          this.client.unsubscribe(replyTopic);
          this.client.removeListener('message', messageHandler);
          console.log('⏰ DO command timeout');
          resolve(false);
        }, 10000);
      });
    });
  }

  /**
   * Reset Counter (DI1-DI4)
   */
  async resetCounter(counter: 1 | 2 | 3 | 4): Promise<boolean> {
    if (!this.authenticated) {
      console.error('❌ Not authenticated. Send password validation first.');
      return false;
    }

    const command = this.buildCounterResetCommand(counter);
    const topic = `uc/${this.deviceId}/ucp/14/cmd/update`;
    
    return new Promise((resolve) => {
      const replyTopic = `uc/${this.deviceId}/ucp/14/cmd/update/accepted`;
      this.client.subscribe(replyTopic, (err: any) => {
        if (err) {
          console.error('❌ Failed to subscribe to reply topic:', err);
          resolve(false);
          return;
        }

        const messageHandler = (topic: string, payload: Buffer) => {
          if (topic === replyTopic) {
            this.client.unsubscribe(replyTopic);
            this.client.removeListener('message', messageHandler);
            
            const response = this.parseCommandResponse(payload);
            if (response && response.result === 0x00) {
              console.log(`✅ Counter${counter} reset command successful`);
              resolve(true);
            } else {
              console.log(`❌ Counter${counter} reset command failed`);
              resolve(false);
            }
          }
        };

        this.client.on('message', messageHandler);

        console.log(`🔢 Sending Counter${counter} reset command to ${topic}`);
        this.client.publish(topic, command, (err: any) => {
          if (err) {
            console.error('❌ Failed to send counter reset command:', err);
            resolve(false);
          }
        });

        setTimeout(() => {
          this.client.unsubscribe(replyTopic);
          this.client.removeListener('message', messageHandler);
          console.log('⏰ Counter reset command timeout');
          resolve(false);
        }, 10000);
      });
    });
  }

  /**
   * Reset All Counters (DI1-DI4)
   */
  async resetAllCounters(): Promise<boolean[]> {
    const results = await Promise.all([
      this.resetCounter(1),
      this.resetCounter(2),
      this.resetCounter(3),
      this.resetCounter(4)
    ]);
    
    console.log('🔢 All counters reset results:', results);
    return results;
  }

  /**
   * Reboot device
   */
  async rebootDevice(): Promise<boolean> {
    if (!this.authenticated) {
      console.error('❌ Not authenticated. Send password validation first.');
      return false;
    }

    const command = this.buildRebootCommand();
    const topic = `uc/${this.deviceId}/ucp/14/cmd/update`;
    
    return new Promise((resolve) => {
      const replyTopic = `uc/${this.deviceId}/ucp/14/cmd/update/accepted`;
      this.client.subscribe(replyTopic, (err: any) => {
        if (err) {
          console.error('❌ Failed to subscribe to reply topic:', err);
          resolve(false);
          return;
        }

        const messageHandler = (topic: string, payload: Buffer) => {
          if (topic === replyTopic) {
            this.client.unsubscribe(replyTopic);
            this.client.removeListener('message', messageHandler);
            
            const response = this.parseCommandResponse(payload);
            if (response) {
              console.log('✅ Reboot command accepted');
              resolve(true);
            } else {
              console.log('❌ Reboot command failed');
              resolve(false);
            }
          }
        };

        this.client.on('message', messageHandler);

        console.log(`🔄 Sending reboot command to ${topic}`);
        this.client.publish(topic, command, (err: any) => {
          if (err) {
            console.error('❌ Failed to send reboot command:', err);
            resolve(false);
          }
        });

        setTimeout(() => {
          this.client.unsubscribe(replyTopic);
          this.client.removeListener('message', messageHandler);
          console.log('⏰ Reboot command timeout');
          resolve(false);
        }, 10000);
      });
    });
  }

  /**
   * Query device parameters
   */
  async queryParameter(queryId: 'signal' | 'sn' | 'hw-version' | 'sw-version'): Promise<any> {
    if (!this.authenticated) {
      console.error('❌ Not authenticated. Send password validation first.');
      return null;
    }

    const command = this.buildQueryCommand(queryId);
    const topic = `uc/${this.deviceId}/ucp/14/cmd/update`;
    
    return new Promise((resolve) => {
      const replyTopic = `uc/${this.deviceId}/ucp/14/cmd/update/accepted`;
      this.client.subscribe(replyTopic, (err: any) => {
        if (err) {
          console.error('❌ Failed to subscribe to reply topic:', err);
          resolve(null);
          return;
        }

        const messageHandler = (topic: string, payload: Buffer) => {
          if (topic === replyTopic) {
            this.client.unsubscribe(replyTopic);
            this.client.removeListener('message', messageHandler);
            
            const response = this.parseQueryResponse(payload, queryId);
            console.log(`✅ Query ${queryId} result:`, response);
            resolve(response);
          }
        };

        this.client.on('message', messageHandler);

        console.log(`🔍 Sending ${queryId} query to ${topic}`);
        this.client.publish(topic, command, (err: any) => {
          if (err) {
            console.error('❌ Failed to send query command:', err);
            resolve(null);
          }
        });

        setTimeout(() => {
          this.client.unsubscribe(replyTopic);
          this.client.removeListener('message', messageHandler);
          console.log('⏰ Query timeout');
          resolve(null);
        }, 10000);
      });
    });
  }

  // Command builders
  private buildPasswordCommand(): Buffer {
    const passwordHex = Buffer.from(this.password, 'ascii');
    const command = Buffer.alloc(11);
    command.writeUInt8(0x7E, 0);  // Start
    command.writeUInt8(0x01, 1);  // Type: password validation
    command.writeUInt16LE(0x0B, 2); // Length: 11
    passwordHex.copy(command, 4); // Password
    command.writeUInt8(0x7E, 10); // End
    return command;
  }

  private buildDOControlCommand(output: 1 | 2, state: 'open' | 'close', duration?: number): Buffer {
    const command = Buffer.alloc(duration ? 12 : 8);
    command.writeUInt8(0x7E, 0);  // Start
    command.writeUInt8(0x05, 1);  // Type: control device
    command.writeUInt16LE(duration ? 0x0C : 0x08, 2); // Length
    command.writeUInt8(0x10, 4);  // Command: control DO
    command.writeUInt8(output, 5); // DO number
    command.writeUInt8(state === 'open' ? 0x01 : 0x00, 6); // State
    
    if (duration) {
      command.writeUInt32LE(duration, 7); // Duration in ms
    }
    
    command.writeUInt8(0x7E, duration ? 11 : 7); // End
    return command;
  }

  private buildCounterResetCommand(counter: 1 | 2 | 3 | 4): Buffer {
    const command = Buffer.alloc(12);
    command.writeUInt8(0x7E, 0);  // Start
    command.writeUInt8(0x05, 1);  // Type: control device
    command.writeUInt16LE(0x0C, 2); // Length: 12
    command.writeUInt8(0xC6, 4);  // Command: counter reset
    command.writeUInt8(counter, 5); // Counter number (1-4)
    command.writeUInt32LE(0x00000000, 6); // Reset to 0
    command.writeUInt8(0x7E, 10); // End
    return command;
  }

  private buildRebootCommand(): Buffer {
    const command = Buffer.alloc(5);
    command.writeUInt8(0x7E, 0);  // Start
    command.writeUInt8(0x02, 1);  // Type: reboot
    command.writeUInt16LE(0x05, 2); // Length: 5
    command.writeUInt8(0x7E, 4);  // End
    return command;
  }

  private buildQueryCommand(queryId: string): Buffer {
    const queryIds = {
      'signal': 0x0E,
      'sn': 0x72,
      'hw-version': 0x73,
      'sw-version': 0x74
    };
    
    const command = Buffer.alloc(6);
    command.writeUInt8(0x7E, 0);  // Start
    command.writeUInt8(0x04, 1);  // Type: parameter query
    command.writeUInt16LE(0x06, 2); // Length: 6
    command.writeUInt8(queryIds[queryId as keyof typeof queryIds], 4); // Query ID
    command.writeUInt8(0x7E, 5);  // End
    return command;
  }

  // Response parsers
  private parseCommandResponse(payload: Buffer): any {
    if (payload.length < 6) return null;
    
    const startFlag = payload.readUInt8(0);
    const type = payload.readUInt8(1);
    const length = payload.readUInt16LE(2);
    const result = payload.readUInt8(4);
    const endFlag = payload.readUInt8(5);
    
    if (startFlag !== 0x7E || endFlag !== 0x7E) return null;
    
    return { type, length, result };
  }

  private parseQueryResponse(payload: Buffer, queryId: string): any {
    if (payload.length < 6) return null;
    
    const startFlag = payload.readUInt8(0);
    const type = payload.readUInt8(1);
    const length = payload.readUInt16LE(2);
    const endFlag = payload.readUInt8(payload.length - 1);
    
    if (startFlag !== 0x7E || endFlag !== 0x7E) return null;
    
    const data = payload.slice(4, payload.length - 1);
    
    switch (queryId) {
      case 'signal':
        return { signal: data.readUInt8(0) };
      case 'sn':
        return { serialNumber: data.toString('ascii') };
      case 'hw-version':
        return { hardwareVersion: data.toString('ascii') };
      case 'sw-version':
        return { softwareVersion: data.toString('ascii') };
      default:
        return { raw: data.toString('hex') };
    }
  }

  // Utility methods
  isAuthenticated(): boolean {
    return this.authenticated;
  }

  resetAuthentication(): void {
    this.authenticated = false;
  }
} 