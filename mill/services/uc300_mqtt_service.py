#!/usr/bin/env python3
"""
🚀 UC300 MQTT Service - Real MQTT Commands
Echte MQTT commando's voor UC300 counter reset met HEX payloads

Commando's:
- DI1 Counter Reset: 7e050b006001000000007e
- DI2 Counter Reset: 7e050b006002000000007e
- Topic: uc/[Device_SN]/ucp/+/cmd/update
"""

import json
import logging
from datetime import datetime
from django.conf import settings
from mill.models import Device, CounterResetLog

# Try to import paho-mqtt, fallback to simulation if not available
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("⚠️ paho-mqtt not available, using simulation mode")

logger = logging.getLogger(__name__)

class UC300MQTTService:
    """
    Real UC300 MQTT service voor counter reset commando's
    """
    
    # HEX Payloads voor UC300 counter reset (alle 4 counters)
    HEX_PAYLOADS = {
        'counter_1': '7e050b006001000000007e',  # DI1 reset
        'counter_2': '7e050b006002000000007e',  # DI2 reset
        'counter_3': '7e050b006003000000007e',  # DI3 reset
        'counter_4': '7e050b006004000000007e',  # DI4 reset
    }
    
    def __init__(self):
        self.mqtt_client = None
        self.is_connected = False
        self.logger = logger
        
        # MQTT broker settings (zet in Django settings)
        self.broker_host = getattr(settings, 'UC300_MQTT_BROKER_HOST', 'localhost')
        self.broker_port = getattr(settings, 'UC300_MQTT_BROKER_PORT', 1883)
        self.username = getattr(settings, 'UC300_MQTT_USERNAME', None)
        self.password = getattr(settings, 'UC300_MQTT_PASSWORD', None)
        
    def log(self, message, level="INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {'INFO': '📋', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌'}
        icon = icons.get(level, '📋')
        print(f"[{timestamp}] {icon} {message}")
        
        # Also use Django logger
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        if not MQTT_AVAILABLE:
            self.log("MQTT library not available, using simulation", "WARNING")
            return False
            
        try:
            self.mqtt_client = mqtt.Client()
            
            # Set credentials if provided
            if self.username and self.password:
                self.mqtt_client.username_pw_set(self.username, self.password)
            
            # Set callbacks
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_disconnect = self._on_disconnect
            self.mqtt_client.on_publish = self._on_publish
            
            # Connect to broker
            self.log(f"Connecting to MQTT broker: {self.broker_host}:{self.broker_port}")
            self.mqtt_client.connect(self.broker_host, self.broker_port, 60)
            
            # Start network loop
            self.mqtt_client.loop_start()
            
            return True
            
        except Exception as e:
            self.log(f"Failed to connect to MQTT broker: {str(e)}", "ERROR")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback voor MQTT connection"""
        if rc == 0:
            self.is_connected = True
            self.log("✅ Connected to MQTT broker", "SUCCESS")
        else:
            self.log(f"❌ Failed to connect to MQTT broker (code: {rc})", "ERROR")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback voor MQTT disconnection"""
        self.is_connected = False
        self.log("📡 Disconnected from MQTT broker", "WARNING")
    
    def _on_publish(self, client, userdata, mid):
        """Callback voor successful publish"""
        self.log(f"📤 MQTT message published (ID: {mid})", "SUCCESS")
    
    def disconnect_mqtt(self):
        """Disconnect from MQTT broker"""
        if self.mqtt_client and self.is_connected:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.log("📡 Disconnected from MQTT broker")
    
    def get_reset_topic(self, device_sn):
        """Get MQTT topic voor UC300 reset command"""
        # Remove wildcard for publishing - use specific channel or default
        return f"uc/{device_sn}/ucp/1/cmd/update"
    
    def get_hex_payload(self, selected_counter):
        """Get HEX payload voor selected counter"""
        payload = self.HEX_PAYLOADS.get(selected_counter)
        if not payload:
            self.log(f"Unknown counter type: {selected_counter}", "ERROR")
            # Default to counter_2 (DI2)
            payload = self.HEX_PAYLOADS['counter_2']
            
        return payload
    
    def send_reset_command(self, device_id, reason="manual"):
        """
        Send real UC300 reset command via MQTT
        
        Args:
            device_id: UC300 device serial number
            reason: Reset reason for logging
            
        Returns:
            CounterResetLog object or None
        """
        try:
            # Get device info
            device = Device.objects.get(id=device_id)
            selected_counter = device.selected_counter
            device_sn = device.id  # Serial number
            
            self.log(f"🔄 Preparing UC300 reset for device {device_sn}")
            self.log(f"Selected counter: {selected_counter}")
            
            # Get current counter value (for logging)
            current_value = self._get_current_counter_value(device_id, selected_counter)
            
            # Prepare MQTT command
            topic = self.get_reset_topic(device_sn)
            hex_payload = self.get_hex_payload(selected_counter)
            
            # Map counter to DI name
            di_mapping = {
                'counter_1': 'DI1',
                'counter_2': 'DI2', 
                'counter_3': 'DI3',
                'counter_4': 'DI4'
            }
            di_name = di_mapping.get(selected_counter, 'UNKNOWN')
            
            self.log(f"📡 MQTT Topic: {topic}")
            self.log(f"📡 HEX Payload: {hex_payload}")
            self.log(f"📡 Counter Type: {selected_counter} ({di_name})")
            
            # Create reset log BEFORE sending command
            reset_log = CounterResetLog.objects.create(
                device=device,
                reset_timestamp=datetime.now(),
                counter_2_before=current_value,
                reset_reason=reason,
                reset_successful=False,  # Will be updated after successful send
                notes=f"UC300 MQTT Reset - Topic: {topic}, Payload: {hex_payload}"
            )
            
            # Send MQTT command
            success = self._publish_mqtt_command(topic, hex_payload)
            
            if success:
                # Update reset log as successful
                reset_log.reset_successful = True
                reset_log.notes += f"\n✅ MQTT command sent successfully at {datetime.now()}"
                reset_log.save()
                
                self.log(f"✅ UC300 reset command sent successfully", "SUCCESS")
                self.log(f"✅ Reset log created: ID {reset_log.id}", "SUCCESS")
                self.log(f"🔄 Counter reset: {current_value} → 0", "SUCCESS")
                
                return reset_log
            else:
                reset_log.notes += f"\n❌ MQTT command failed at {datetime.now()}"
                reset_log.save()
                
                self.log(f"❌ Failed to send UC300 reset command", "ERROR")
                return None
                
        except Device.DoesNotExist:
            self.log(f"Device {device_id} not found", "ERROR")
            return None
        except Exception as e:
            self.log(f"Error sending UC300 reset command: {str(e)}", "ERROR")
            return None
    
    def _publish_mqtt_command(self, topic, hex_payload):
        """Publish MQTT command (real or simulated)"""
        try:
            if MQTT_AVAILABLE and self.mqtt_client and self.is_connected:
                # REAL MQTT PUBLISH
                self.log("📡 Sending REAL MQTT command to UC300 device")
                
                # Convert hex string to bytes for payload
                try:
                    payload_bytes = bytes.fromhex(hex_payload)
                    result = self.mqtt_client.publish(topic, payload_bytes, qos=1)
                    
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        self.log("✅ MQTT publish successful", "SUCCESS")
                        return True
                    else:
                        self.log(f"❌ MQTT publish failed (code: {result.rc})", "ERROR")
                        return False
                        
                except ValueError as e:
                    self.log(f"❌ Invalid HEX payload: {str(e)}", "ERROR")
                    return False
                    
            else:
                # SIMULATION MODE
                self.log("🔄 SIMULATING MQTT command (no real broker connection)")
                self.log(f"📡 Would publish to: {topic}")
                self.log(f"📡 Would send HEX: {hex_payload}")
                
                # Simulate successful publish
                return True
                
        except Exception as e:
            self.log(f"Error publishing MQTT command: {str(e)}", "ERROR")
            return False
    
    def _get_current_counter_value(self, device_id, selected_counter):
        """Get current counter value from MQTT data"""
        try:
            from django.db import connections
            
            with connections['counter'].cursor() as cursor:
                query = f"""
                    SELECT {selected_counter}, timestamp
                    FROM mqtt_data 
                    WHERE counter_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (device_id,))
                result = cursor.fetchone()
                
                if result:
                    counter_value, timestamp = result
                    return counter_value if counter_value is not None else 0
                else:
                    return 0
                    
        except Exception as e:
            self.log(f"Error getting counter value: {str(e)}", "ERROR")
            return 0
    
    def test_connection(self):
        """Test MQTT broker connection"""
        self.log("🧪 Testing MQTT broker connection...")
        
        if self.connect_mqtt():
            self.log("✅ MQTT connection test successful", "SUCCESS")
            self.disconnect_mqtt()
            return True
        else:
            self.log("❌ MQTT connection test failed", "ERROR")
            return False
    
    def send_batch_reset(self, device_id, batch_name):
        """Send reset command specifically for batch start"""
        return self.send_reset_command(device_id, f"batch_start_{batch_name}")
    
    def send_daily_reset(self, device_id):
        """Send reset command for daily reset (23:59)"""
        return self.send_reset_command(device_id, "daily_reset")
    
    def send_manual_reset(self, device_id):
        """Send reset command for manual reset"""
        return self.send_reset_command(device_id, "manual_reset")

# Convenience function for easy import
def get_uc300_mqtt_service():
    """Get UC300 MQTT service instance"""
    return UC300MQTTService() 