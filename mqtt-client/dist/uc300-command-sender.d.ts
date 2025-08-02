import { MqttClient } from 'mqtt';
export interface UC300Command {
    type: 'password' | 'reboot' | 'do-control' | 'query' | 'report-interval' | 'counter-reset';
    data?: any;
}
export declare class UC300CommandSender {
    private client;
    private deviceId;
    private password;
    private authenticated;
    constructor(client: MqttClient, deviceId: string, password?: string);
    /**
     * Send password validation (required before other commands)
     */
    sendPasswordValidation(): Promise<boolean>;
    /**
     * Control Digital Output
     */
    controlDigitalOutput(output: 1 | 2, state: 'open' | 'close', duration?: number): Promise<boolean>;
    /**
     * Reset Counter (DI1-DI4)
     */
    resetCounter(counter: 1 | 2 | 3 | 4): Promise<boolean>;
    /**
     * Reset All Counters (DI1-DI4)
     */
    resetAllCounters(): Promise<boolean[]>;
    /**
     * Reboot device
     */
    rebootDevice(): Promise<boolean>;
    /**
     * Query device parameters
     */
    queryParameter(queryId: 'signal' | 'sn' | 'hw-version' | 'sw-version'): Promise<any>;
    private buildPasswordCommand;
    private buildDOControlCommand;
    private buildCounterResetCommand;
    private buildRebootCommand;
    private buildQueryCommand;
    private parseCommandResponse;
    private parseQueryResponse;
    isAuthenticated(): boolean;
    resetAuthentication(): void;
}
//# sourceMappingURL=uc300-command-sender.d.ts.map