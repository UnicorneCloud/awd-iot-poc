from chalice import Chalice
import pickle
import logging
import base64
import boto3
import json
import secrets
import uuid
from db import DeviceDB

app = Chalice(app_name='iot-poc')

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize in-memory database for devices
device_db = DeviceDB()

# Initialize IoT client
iot_client = boto3.client('iot')

@app.lambda_function()
def handle_iot_message(event, context):
  """
  AWS Lambda function to process a pickled Python serialization from an IoT message.
  """
  try:
    # Assume the pickled data is passed in the event body
    pickled_data = event.get('data')
    if not pickled_data:
      logger.error("No pickled data found in the event body.")
      return {
        'statusCode': 400,
        'body': 'No pickled data provided.'
      }

    # Decode the base64-encoded pickled data
    try:
      decoded_data = base64.b64decode(pickled_data)
      # Deserialize the pickled data
      deserialized_data = pickle.loads(decoded_data)
      logger.info("Deserialized data: %s", deserialized_data)

      return {
        'statusCode': 200,
        'body': 'Message processed successfully.'
      }
    except TypeError as e:
      logger.error("Base64 decoding error: %s", e)
      return {
        'statusCode': 400,
        'body': 'Invalid base64 encoded data.'
      }

  except pickle.UnpicklingError as e:
    logger.error("Failed to unpickle data: %s", e)
    return {
      'statusCode': 400,
      'body': 'Invalid pickled data.'
    }
  except Exception as e:
    logger.error("An error occurred: %s", e)
    return {
      'statusCode': 500,
      'body': 'Internal server error.'
    }

@app.route('/register-device', methods=['POST'])
def register_device():
    """
    API endpoint to register a new device with AWS IoT Core.
    Expects JSON body with:
    - device_id: Unique identifier for the device
    - secret_key: Pre-shared secret key given to device at shipping time
    """
    try:
        request_body = app.current_request.json_body
        
        if not request_body or 'device_id' not in request_body or 'secret_key' not in request_body:
            logger.error("Invalid request body")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields: device_id and secret_key'})
            }
        
        device_id = request_body['device_id']
        secret_key = request_body['secret_key']
        
        # Check if device exists in database with matching secret
        if not device_db.verify_device(device_id, secret_key):
            logger.error(f"Device verification failed for device: {device_id}")
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Device verification failed'})
            }
        
        # Generate a unique thing name (can be based on device_id)
        thing_name = f"device-{device_id}"
        
        # Register the thing with AWS IoT Core
        try:
            # Create thing in IoT Core
            iot_client.create_thing(
                thingName=thing_name,
                attributePayload={
                    'attributes': {
                        'device_id': device_id
                    }
                }
            )
            
            # Create certificate and attach to thing
            certificate_response = iot_client.create_keys_and_certificate(setAsActive=True)
            
            cert_id = certificate_response['certificateId']
            cert_arn = certificate_response['certificateArn']
            cert_pem = certificate_response['certificatePem']
            private_key = certificate_response['keyPair']['PrivateKey']
            
            # Attach certificate to thing
            iot_client.attach_thing_principal(
                thingName=thing_name,
                principal=cert_arn
            )
            
            # Create and attach policy to certificate
            policy_name = f"device-policy-{device_id}"
            
            # Create policy document allowing publish/subscribe
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "iot:Connect",
                            "iot:Publish",
                            "iot:Subscribe",
                            "iot:Receive"
                        ],
                        "Resource": [
                            f"arn:aws:iot:*:*:topic/device/{device_id}/*",
                            f"arn:aws:iot:*:*:client/{thing_name}"
                        ]
                    }
                ]
            }
            
            # Create policy
            try:
                iot_client.create_policy(
                    policyName=policy_name,
                    policyDocument=json.dumps(policy_document)
                )
            except iot_client.exceptions.ResourceAlreadyExistsException:
                logger.info(f"Policy {policy_name} already exists")
            
            # Attach policy to certificate
            iot_client.attach_policy(
                policyName=policy_name,
                target=cert_arn
            )
            
            # Return certificate and endpoint information
            endpoint_response = iot_client.describe_endpoint(endpointType='iot:Data-ATS')
            
            # Update the device in DB as registered
            device_db.mark_as_registered(device_id, thing_name)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Device registered successfully',
                    'thingName': thing_name,
                    'certificateId': cert_id,
                    'certificatePem': cert_pem,
                    'privateKey': private_key,
                    'endpoint': endpoint_response['endpointAddress']
                })
            }
            
        except Exception as e:
            logger.error(f"Error registering device with IoT Core: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to register device: {str(e)}'})
            }
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

# Helper endpoints for testing and management
@app.route('/seed-device', methods=['POST'])
def seed_device():
    """
    API endpoint to seed the device database with a new device entry.
    In production, this would be replaced with a more secure provisioning process.
    """
    try:
        request_body = app.current_request.json_body
        
        if not request_body or 'device_id' not in request_body:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required field: device_id'})
            }
        
        device_id = request_body['device_id']
        # Generate a random secret for the device
        secret_key = secrets.token_hex(16)
        
        # Add to database
        device_db.add_device(device_id, secret_key)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'device_id': device_id,
                'secret_key': secret_key
            })
        }
        
    except Exception as e:
        logger.error(f"Error seeding device: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
