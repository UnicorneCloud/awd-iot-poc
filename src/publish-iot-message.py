import pickle
import random
import time
import requests
import json
import argparse
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Publish IoT messages to AWS IoT Core")
    parser.add_argument("--config", required=True, help="Path to the configuration JSON file")
    parser.add_argument("--interval", type=int, default=5, help="Interval between messages in seconds (default: 5)")
    parser.add_argument("--topic", required=True, help="Custom topic to publish messages to (overrides default topic)")
    return parser.parse_args()

def load_config(config_path):
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get the directory of the config file for relative paths
        config_dir = os.path.dirname(os.path.abspath(config_path))
        
        # Convert relative paths to absolute paths
        for key in ['certificate_path', 'private_key_path', 'root_ca_path']:
            if key in config and not os.path.isabs(config[key]):
                config[key] = os.path.join(config_dir, config[key])
                
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise e

def generate_temperature(mean=80, std_dev=10):
    """
    Generate a temperature value using a normal distribution.
    The temperature is constrained between 40 and 120 degrees Celsius.
    """
    while True:
        temperature = random.gauss(mean, std_dev)
        if 40 <= temperature <= 120:
            return temperature

def publish_iot_message(endpoint_url, device_id, topic, root_cert, cert_pem, private_pem):
    """
    Publish a pickled message containing a temperature value to an AWS IoT HTTPS endpoint.
    """
    # Generate temperature
    temperature = generate_temperature()

    # Create the message
    message = {
        "device_id": device_id,
        "temperature": temperature,
    }

    # Pickle the message
    pickled_message = pickle.dumps(message)

    # Define headers
    headers = {
        'Content-Type': 'application/octet-stream',
        # 'Content-Type': 'application/json'
    }

    # Send the request
    try:
        # create and format values for HTTPS request
        publish_url = 'https://' + endpoint_url + ':8443/topics/' + topic + '?qos=1'
        # make request
        publish = requests.request('POST',
                    publish_url,
                    headers=headers,
                    # data=json.dumps(message).encode('utf-8'),
                    data=pickled_message,
                    verify=root_cert,
                    cert=(cert_pem, private_pem)
                )
        if publish.status_code != 200:
          logger.error(f"Failed to publish message. Status code: {publish.status_code}")
          logger.error(f"Response: {publish.text}")
          return
        else:
          logger.info(f"Message published with: {publish.status_code}")
          logger.info(f"Temperature: {temperature:.2f}°C")
          logger.debug(f"Response:\n{publish.text}")
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")
        raise e

def main():
    """
    Main function to run the script with command line arguments.
    """
    args = parse_args()
    config = load_config(args.config)
    
    # Extract parameters from config
    endpoint_url = config.get("endpoint")
    device_id = config.get("device_id")
    
    # Use custom topic if provided, otherwise construct the default topic
    topic = args.topic
        
    root_cert = config.get("root_ca_path")
    cert_pem = config.get("certificate_path")
    private_pem = config.get("private_key_path")
    
    logger.info(f"Publishing messages for device: {device_id}")
    logger.info(f"Using endpoint: {endpoint_url}")
    logger.info(f"Publishing to topic: {topic}")
    
    try:
        while True:
            publish_iot_message(endpoint_url, device_id, topic, root_cert, cert_pem, private_pem)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Script terminated by user")
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())