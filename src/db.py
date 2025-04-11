"""
In-memory device database module.
This is a simplified implementation for demonstration purposes.
In a production environment, this would be replaced with a persistent database solution.
"""
import logging
from datetime import datetime

logger = logging.getLogger()

class DeviceDB:
    """Simple in-memory database for IoT device registration and verification."""
    
    def __init__(self):
        """Initialize an empty device database."""
        # Structure:
        # {
        #   'device_id': {
        #     'secret_key': 'secret123',
        #     'registration_status': 'pending|registered',
        #     'thing_name': 'aws-iot-thing-name',  # Only set after registration
        #     'created_at': datetime,
        #     'registered_at': datetime  # Only set after registration
        #   }
        # }
        self.devices = {}
        logger.info("In-memory device database initialized")
    
    def add_device(self, device_id, secret_key):
        """
        Add a new device to the database with pending registration status.
        
        Args:
            device_id (str): Unique identifier for the device
            secret_key (str): Secret key to be used for verification
            
        Returns:
            bool: True if device was added successfully, False otherwise
        """
        if device_id in self.devices:
            logger.warning(f"Device ID {device_id} already exists in database")
            return False
        
        self.devices[device_id] = {
            'secret_key': secret_key,
            'registration_status': 'pending',
            'thing_name': None,
            'created_at': datetime.utcnow(),
            'registered_at': None
        }
        
        logger.info(f"Added device {device_id} to database")
        return True
    
    def verify_device(self, device_id, secret_key):
        """
        Verify if a device exists and the secret key matches.
        
        Args:
            device_id (str): Device ID to verify
            secret_key (str): Secret key to check
            
        Returns:
            bool: True if device exists and secret matches, False otherwise
        """
        if device_id not in self.devices:
            logger.warning(f"Device ID {device_id} not found in database")
            return False
            
        device = self.devices[device_id]
        if device['secret_key'] != secret_key:
            logger.warning(f"Invalid secret key for device {device_id}")
            return False
            
        return True
    
    def mark_as_registered(self, device_id, thing_name):
        """
        Mark a device as registered with AWS IoT Core.
        
        Args:
            device_id (str): Device ID to update
            thing_name (str): AWS IoT thing name assigned to the device
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if device_id not in self.devices:
            logger.warning(f"Cannot mark non-existent device {device_id} as registered")
            return False
            
        self.devices[device_id]['registration_status'] = 'registered'
        self.devices[device_id]['thing_name'] = thing_name
        self.devices[device_id]['registered_at'] = datetime.now(datetime.timezone.utc)
        
        logger.info(f"Device {device_id} marked as registered with thing name {thing_name}")
        return True
    
    def get_device(self, device_id):
        """
        Get device information.
        
        Args:
            device_id (str): Device ID to retrieve
            
        Returns:
            dict: Device information or None if not found
        """
        if device_id not in self.devices:
            return None
            
        return self.devices[device_id]
    
    def get_all_devices(self):
        """
        Get all devices in the database.
        
        Returns:
            dict: All devices
        """
        return self.devices