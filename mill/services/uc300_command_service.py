"""
🔄 UC300 Command Service - Pilot System
Service for sending commands to UC300 devices via MQTT
"""

import json
import logging
import datetime
from typing import Optional, Dict, Any
from django.utils import timezone
from django.conf import settings
import paho.mqtt.client as mqtt
import threading
import time

from mill.models import Device, CounterResetLog, UC300PilotStatus

logger = logging.getLogger(__name__)

class UC300CommandService:
    """
    Service for sending commands to UC300 devices via MQTT.
    This is part of the pilot system for counter resets.
    """
    
    def __init__(self):
        self.mqtt_client = None
        self.is_connected = False
        self.command_responses = {}  # Track command responses
        self.connection_lock = threading.Lock()
        
        # MQTT Configuration
        self.broker_host = getattr(settings, 'MQTT_BROKER_HOST', 'mqtt-broker')
        self.broker_port = getattr(settings, 'MQTT_BROKER_PORT', 1883)
        self.username = getattr(settings, 'MQTT_USERNAME', 'uc300')
        self.password = getattr(settings, 'MQTT_PASSWORD', 'grain300')
        
        self._setup_mqtt_client()
    
    def _setup_mqtt_client(self):
        """Setup MQTT client with callbacks"""
        try:
            self.mqtt_client = mqtt.Client(client_id="UC300_Command_Service", protocol=mqtt.MQTTv5)
            
            # Set credentials
            if self.username and self.password:
                self.mqtt_client.username_pw_set(self.username, self.password)
            
            # Set callbacks
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_disconnect = self._on_disconnect
            self.mqtt_client.on_message = self._on_message
            self.mqtt_client.on_publish = self._on_publish
            
            logger.info("UC300 Command Service MQTT client configured")
            
        except Exception as e:
            logger.error(f"Error setting up MQTT client: {str(e)}")
            raise
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.is_connected = True
            logger.info("UC300 Command Service connected to MQTT broker")
            
            # Subscribe to command response topics
            response_topics = [
                "uc/+/ucp/command/response",
                "uc/+/ucp/reset/response",
                "uc/+/ucp/status/response"
            ]
            
            for topic in response_topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to command response topic: {topic}")
        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.is_connected = False
        logger.warning(f"Disconnected from MQTT broker, return code {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for received MQTT messages (command responses)"""
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 3:
                device_id = topic_parts[1]
                
                # Decode response payload
                try:
                    response = json.loads(msg.payload.decode('utf-8'))
                    self.command_responses[device_id] = {
                        'timestamp': datetime.datetime.now(),
                        'topic': msg.topic,
                        'response': response
                    }
                    logger.info(f"Received command response from {device_id}: {response}")
                except json.JSONDecodeError:
                    # Handle binary responses if needed
                    logger.warning(f"Received non-JSON response from {device_id}")
                    
        except Exception as e:
            logger.error(f"Error processing command response: {str(e)}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for published messages"""
        logger.debug(f"Command published with message ID: {mid}")
    
    def connect(self, timeout=10):
        """Connect to MQTT broker"""
        with self.connection_lock:
            if self.is_connected:
                return True
            
            try:
                logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
                self.mqtt_client.connect(self.broker_host, self.broker_port, 60)
                self.mqtt_client.loop_start()
                
                # Wait for connection
                start_time = time.time()
                while not self.is_connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if self.is_connected:
                    logger.info("Successfully connected to MQTT broker")
                    return True
                else:
                    logger.error("Failed to connect to MQTT broker within timeout")
                    return False
                    
            except Exception as e:
                logger.error(f"Error connecting to MQTT broker: {str(e)}")
                return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        with self.connection_lock:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                self.is_connected = False
                logger.info("Disconnected from MQTT broker")
    
    def send_reset_command(self, device_id: str, counter_number: int = 2, 
                          reset_reason: str = 'manual') -> bool:
        """
        Send counter reset command to UC300 device
        
        Args:
            device_id: UC300 device ID
            counter_number: Counter to reset (1-4)
            reset_reason: Reason for reset
            
        Returns:
            bool: True if command sent successfully
        """
        try:
            # Ensure connection
            if not self.is_connected:
                if not self.connect():
                    return False
            
            # Get current counter value before reset
            current_values = self._get_current_counter_values(device_id)
            
            # Prepare reset command
            command_topic = f"uc/{device_id}/ucp/command/reset"
            command_payload = {
                "command": "reset_counter",
                "counter": counter_number,
                "value": 0,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "reason": reset_reason
            }
            
            # Send command
            payload_json = json.dumps(command_payload)
            result = self.mqtt_client.publish(command_topic, payload_json, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Reset command sent to {device_id}, counter {counter_number}")
                
                # Log the reset attempt
                self._log_reset_attempt(device_id, counter_number, current_values, reset_reason)
                
                return True
            else:
                logger.error(f"Failed to send reset command to {device_id}, error: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending reset command to {device_id}: {str(e)}")
            return False
    
    def send_batch_reset_command(self, device_id: str, batch_name: str = None) -> bool:
        """
        Send batch reset command (resets all production counters)
        
        Args:
            device_id: UC300 device ID
            batch_name: Optional batch identifier
            
        Returns:
            bool: True if command sent successfully
        """
        try:
            # Get current values before reset
            current_values = self._get_current_counter_values(device_id)
            
            # Send reset commands for all production counters (typically counter_2)
            device = Device.objects.filter(id=device_id).first()
            if device:
                selected_counter = getattr(device, 'selected_counter', 'counter_2')
                counter_num = int(selected_counter.split('_')[1])
                
                success = self.send_reset_command(device_id, counter_num, 'batch_start')
                
                if success and batch_name:
                    # Send batch start notification
                    batch_topic = f"uc/{device_id}/ucp/batch/start"
                    batch_payload = {
                        "batch_name": batch_name,
                        "start_time": datetime.datetime.utcnow().isoformat(),
                        "reset_counters": [counter_num]
                    }
                    
                    self.mqtt_client.publish(batch_topic, json.dumps(batch_payload), qos=1)
                    logger.info(f"Batch start notification sent for {device_id}: {batch_name}")
                
                return success
            else:
                logger.error(f"Device {device_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error sending batch reset command to {device_id}: {str(e)}")
            return False
    
    def schedule_daily_reset(self, device_id: str, reset_time: str = "06:00") -> bool:
        """
        Schedule daily reset for a device
        
        Args:
            device_id: UC300 device ID
            reset_time: Time to reset (HH:MM format)
            
        Returns:
            bool: True if schedule set successfully
        """
        try:
            # This would integrate with a scheduling system (e.g., Celery)
            # For now, just log the intent
            logger.info(f"Daily reset scheduled for {device_id} at {reset_time}")
            
            # Update pilot status
            device = Device.objects.filter(id=device_id).first()
            if device:
                pilot_status, created = UC300PilotStatus.objects.get_or_create(device=device)
                pilot_status.daily_reset_time = reset_time
                pilot_status.save()
                
                logger.info(f"Daily reset time updated for {device_id}: {reset_time}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error scheduling daily reset for {device_id}: {str(e)}")
            return False
    
    def _get_current_counter_values(self, device_id: str) -> Dict[str, Any]:
        """Get current counter values from database"""
        try:
            from django.db import connections
            
            with connections['counter'].cursor() as cursor:
                query = """
                    SELECT counter_1, counter_2, counter_3, counter_4, timestamp
                    FROM mqtt_data 
                    WHERE counter_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (device_id,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'counter_1': result[0],
                        'counter_2': result[1], 
                        'counter_3': result[2],
                        'counter_4': result[3],
                        'timestamp': result[4]
                    }
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting current counter values for {device_id}: {str(e)}")
            return {}
    
    def _log_reset_attempt(self, device_id: str, counter_number: int, 
                          current_values: Dict, reset_reason: str):
        """Log reset attempt to database"""
        try:
            device = Device.objects.filter(id=device_id).first()
            if not device:
                logger.error(f"Device {device_id} not found for reset logging")
                return
            
            # Create reset log entry
            reset_log = CounterResetLog.objects.create(
                device=device,
                reset_timestamp=timezone.now(),
                counter_1_before=current_values.get('counter_1'),
                counter_2_before=current_values.get('counter_2'),
                counter_3_before=current_values.get('counter_3'),
                counter_4_before=current_values.get('counter_4'),
                reset_reason=reset_reason,
                reset_successful=False,  # Will be updated when response received
                notes=f"Reset command sent for counter {counter_number}"
            )
            
            logger.info(f"Reset attempt logged: {reset_log.id}")
            
        except Exception as e:
            logger.error(f"Error logging reset attempt: {str(e)}")
    
    def verify_reset_success(self, device_id: str, timeout: int = 30) -> bool:
        """
        Verify that a reset was successful by checking for response
        
        Args:
            device_id: UC300 device ID
            timeout: Timeout in seconds
            
        Returns:
            bool: True if reset was verified successful
        """
        try:
            start_time = time.time()
            
            while (time.time() - start_time) < timeout:
                if device_id in self.command_responses:
                    response_data = self.command_responses[device_id]
                    response = response_data.get('response', {})
                    
                    if response.get('status') == 'success' and response.get('command') == 'reset_counter':
                        logger.info(f"Reset verified successful for {device_id}")
                        
                        # Update reset log
                        self._update_reset_log_success(device_id)
                        
                        return True
                
                time.sleep(1)
            
            logger.warning(f"Reset verification timeout for {device_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying reset for {device_id}: {str(e)}")
            return False
    
    def _update_reset_log_success(self, device_id: str):
        """Update reset log to mark as successful"""
        try:
            device = Device.objects.filter(id=device_id).first()
            if device:
                # Get the most recent reset log for this device
                recent_reset = CounterResetLog.objects.filter(
                    device=device
                ).order_by('-created_at').first()
                
                if recent_reset and not recent_reset.reset_successful:
                    recent_reset.reset_successful = True
                    recent_reset.notes += " - Reset verified successful"
                    recent_reset.save()
                    
                    logger.info(f"Reset log updated as successful: {recent_reset.id}")
                    
        except Exception as e:
            logger.error(f"Error updating reset log for {device_id}: {str(e)}")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Convenience functions for external use
def reset_device_counter(device_id: str, counter_number: int = 2, 
                        reset_reason: str = 'manual') -> bool:
    """
    Convenience function to reset a device counter
    
    Args:
        device_id: UC300 device ID
        counter_number: Counter to reset (1-4)
        reset_reason: Reason for reset
        
    Returns:
        bool: True if reset successful
    """
    with UC300CommandService() as service:
        success = service.send_reset_command(device_id, counter_number, reset_reason)
        if success:
            # Wait for verification
            return service.verify_reset_success(device_id)
        return False


def reset_device_for_batch(device_id: str, batch_name: str = None) -> bool:
    """
    Convenience function to reset device for new batch
    
    Args:
        device_id: UC300 device ID
        batch_name: Optional batch identifier
        
    Returns:
        bool: True if reset successful
    """
    with UC300CommandService() as service:
        return service.send_batch_reset_command(device_id, batch_name) 