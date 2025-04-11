#!/usr/bin/env python3
import os
import json
import requests
import argparse
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Register a device with AWS IoT Core")
    parser.add_argument("--device-id", required=True, help="Unique device ID for registration")
    parser.add_argument("--api-url", required=True, help="API Gateway URL (e.g., https://abc123.execute-api.region.amazonaws.com/api)")
    parser.add_argument("--api-key", required=True, help="API Key for authentication")
    parser.add_argument("--output-dir", default=".", help="Directory to save certificates (default: current directory)")
    return parser.parse_args()

def register_device(api_url, api_key, device_id):
    """
    First create a new device in the database, then register it with AWS IoT Core.
    
    Args:
        api_url (str): API Gateway URL
        api_key (str): API Key for authentication
        device_id (str): Unique device ID
        
    Returns:
        dict: Registration response containing certificate information
    """
    # Ensure API URL is properly formatted
    api_base_url = api_url.rstrip("/")
    
    # Headers for API requests
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    # Step 1: Seed the device to create an entry in the database
    seed_url = f"{api_base_url}/seed-device"
    seed_data = {"device_id": device_id}
    
    logger.info(f"Seeding device with ID: {device_id}")
    seed_response = requests.post(
        seed_url,
        headers=headers,
        json=seed_data
    )
    
    if seed_response.status_code != 200:
        error_msg = f"Failed to seed device: {seed_response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    seed_result = seed_response.json()
    response_body = json.loads(seed_result.get("body"))
    print("Body:", response_body)
    secret_key = response_body.get("secret_key")
    
    if not secret_key:
        error_msg = "No secret key returned from seeding operation"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    logger.info(f"Device seeded successfully. Secret key: {secret_key}")
    
    # Step 2: Register the device with AWS IoT Core
    register_url = f"{api_base_url}/register-device"
    register_data = {
        "device_id": device_id,
        "secret_key": secret_key
    }
    
    logger.info(f"Registering device with ID: {device_id}")
    register_response = requests.post(
        register_url,
        headers=headers,
        json=register_data
    )
    print("Register Response:", register_response.json())
    
    if register_response.status_code != 200:
        error_msg = f"Failed to register device: {register_response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    logger.info("Device registered successfully")
    return register_response.json()

def save_certificates(registration_data, device_id, output_dir):
    """
    Save certificates and configuration files to a timestamped directory.
    
    Args:
        registration_data (dict): Registration response data containing certificates
        device_id (str): Device ID
        output_dir (str): Base output directory
        
    Returns:
        str: Path to the certificate directory
    """
    # Create timestamped directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    cert_dir = os.path.join(output_dir, f"permission_{device_id}_{timestamp}")
    os.makedirs(cert_dir, exist_ok=True)
    
    # Extract certificate data
    cert_pem = registration_data["certificatePem"]
    private_key = registration_data["privateKey"]
    endpoint = registration_data["endpoint"]
    thing_name = registration_data["thingName"]
    
    # Save certificate files
    with open(os.path.join(cert_dir, "certificate.pem"), "w") as f:
        f.write(cert_pem)
    
    with open(os.path.join(cert_dir, "private.key"), "w") as f:
        f.write(private_key)
    
    # Download root CA certificate
    ca_url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
    ca_response = requests.get(ca_url)
    if ca_response.status_code == 200:
        with open(os.path.join(cert_dir, "root-CA.crt"), "w") as f:
            f.write(ca_response.text)
    else:
        logger.warning(f"Failed to download root CA certificate: {ca_response.status_code}")
    
    # Create a config file with connection details
    config = {
        "device_id": device_id,
        "thing_name": thing_name,
        "endpoint": endpoint,
        "certificate_path": "certificate.pem",
        "private_key_path": "private.key",
        "root_ca_path": "root-CA.crt"
    }
    
    with open(os.path.join(cert_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=4)
    
    return cert_dir

def main():
    """Main function to register a device and save its certificates."""
    args = parse_args()
    
    try:
        # Register the device
        registration_data = register_device(args.api_url, args.api_key, args.device_id)
        
        # Save certificates
        cert_dir = save_certificates(registration_data, args.device_id, args.output_dir)
        
        logger.info(f"Device registration complete. Certificates saved to: {cert_dir}")
        print(f"\nDevice Registration Successful")
        print(f"Device ID: {args.device_id}")
        print(f"Thing Name: {registration_data['thingName']}")
        print(f"Certificate files saved to: {cert_dir}")
        print(f"\nCertificate files:")
        print(f"- certificate.pem: Device certificate")
        print(f"- private.key: Device private key")
        print(f"- root-CA.crt: AWS IoT Root CA certificate")
        print(f"- config.json: Device configuration")
        
    except Exception as e:
        logger.error(f"Error during device registration: {str(e)}")
        print(f"Failed to register device: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())