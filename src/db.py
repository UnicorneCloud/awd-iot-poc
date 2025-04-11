"""
Device database module using DynamoDB.
This implementation uses AWS DynamoDB for persistent device storage.
"""
import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
import os

logger = logging.getLogger()

class DeviceDB:
    """DynamoDB-based database for IoT device registration and verification."""
    
    def __init__(self):
        """Initialize DynamoDB connection and ensure table exists."""
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('DEVICES_TABLE_NAME', 'IoTDevices')
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"DynamoDB device database initialized with table {self.table_name}")
    
    def add_device(self, device_id, secret_key):
        """
        Add a new device to the database with pending registration status.
        
        Args:
            device_id (str): Unique identifier for the device
            secret_key (str): Secret key to be used for verification
            
        Returns:
            bool: True if device was added successfully, False otherwise
        """
        try:
            # Check if device already exists
            response = self.table.get_item(Key={'device_id': device_id})
            if 'Item' in response:
                logger.warning(f"Device ID {device_id} already exists in database")
                return False
            
            # Add new device
            current_time = datetime.now(datetime.timezone.utc).isoformat()
            self.table.put_item(
                Item={
                    'device_id': device_id,
                    'secret_key': secret_key,
                    'registration_status': 'pending',
                    'thing_name': None,
                    'created_at': current_time,
                    'registered_at': None
                }
            )
            
            logger.info(f"Added device {device_id} to database")
            return True
            
        except Exception as e:
            logger.error(f"Error adding device to DynamoDB: {str(e)}")
            return False
    
    def verify_device(self, device_id, secret_key):
        """
        Verify a device's identity using its secret key.
        
        Args:
            device_id (str): Device ID to verify
            secret_key (str): Secret key to verify
            
        Returns:
            bool: True if device exists and secret key matches, False otherwise
        """
        try:
            response = self.table.get_item(Key={'device_id': device_id})
            
            if 'Item' not in response:
                logger.warning(f"Device {device_id} not found in database")
                return False
                
            stored_secret = response['Item'].get('secret_key')
            if stored_secret != secret_key:
                logger.warning(f"Secret key mismatch for device {device_id}")
                return False
                
            logger.info(f"Device {device_id} verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying device in DynamoDB: {str(e)}")
            return False
    
    def mark_as_registered(self, device_id, thing_name):
        """
        Mark a device as registered with AWS IoT Core.
        
        Args:
            device_id (str): Device ID to update
            thing_name (str): AWS IoT thing name assigned to the device
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Check if device exists
            response = self.table.get_item(Key={'device_id': device_id})
            if 'Item' not in response:
                logger.warning(f"Cannot mark non-existent device {device_id} as registered")
                return False
            
            # Update device registration status
            current_time = datetime.now(datetime.timezone.utc).isoformat()
            self.table.update_item(
                Key={'device_id': device_id},
                UpdateExpression="SET registration_status = :status, thing_name = :thing_name, registered_at = :time",
                ExpressionAttributeValues={
                    ':status': 'registered',
                    ':thing_name': thing_name,
                    ':time': current_time
                }
            )
            
            logger.info(f"Device {device_id} marked as registered with thing name {thing_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating device in DynamoDB: {str(e)}")
            return False
    
    def get_device(self, device_id):
        """
        Get device information.
        
        Args:
            device_id (str): Device ID to retrieve
            
        Returns:
            dict: Device information or None if not found
        """
        try:
            response = self.table.get_item(Key={'device_id': device_id})
            if 'Item' not in response:
                return None
                
            return response['Item']
            
        except Exception as e:
            logger.error(f"Error retrieving device from DynamoDB: {str(e)}")
            return None
    
    def get_all_devices(self):
        """
        Get all devices in the database.
        
        Returns:
            list: List of all device items
        """
        try:
            response = self.table.scan()
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error scanning devices in DynamoDB: {str(e)}")
            return []