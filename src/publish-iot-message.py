import pickle
import json
import random
import time
import requests

def generate_temperature(mean=80, std_dev=10):
  """
  Generate a temperature value using a normal distribution.
  The temperature is constrained between 40 and 120 degrees Celsius.
  """
  while True:
    temperature = random.gauss(mean, std_dev)
    if 40 <= temperature <= 120:
      return temperature

def publish_iot_message(endpoint_url, topic, root_cert, cert_pem, private_pem):
  """
  Publish a pickled message containing a temperature value to an AWS IoT HTTPS endpoint.
  """
  # Generate temperature
  temperature = generate_temperature()

  # Create the message
  message = {
    "temperature": temperature
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
                data=pickled_message,
                verify=root_cert,
                cert=(cert_pem, private_pem)
              )
    print(f"Message published successfully: {publish.status_code}")
    print(f"Response:\n{publish.text}")
  except Exception as e:
    print(f"Failed to publish message: {e}")
    raise e

def main():
  """
  Main function to run the script locally.
  """
  # Replace these with your actual AWS IoT endpoint and credentials
  endpoint_url = "a3o7h8u7phyoa3-ats.iot.ca-central-1.amazonaws.com"
  topic = "sdk/test/python"

  root_cert = "./perm_files/root-CA.crt"
  cert_pem = "./perm_files/my_mac_test_temp.cert.pem"
  private_pem = "./perm_files/my_mac_test_temp.private.key"

  while True:
    publish_iot_message(endpoint_url, topic, root_cert, cert_pem, private_pem)
    time.sleep(5)

if __name__ == "__main__":
  main()