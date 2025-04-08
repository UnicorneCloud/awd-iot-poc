import base64
import json
import pickle
import sys

def encode_with_base64_and_json(data):
  """Encodes data using JSON and Base64."""
  json_data = json.dumps(data)
  base64_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
  return base64_data

def encode_with_json(data):
  """Encodes data using JSON."""
  json_data = json.dumps(data)
  return json_data

def encode_with_pickle(data):
  """Encodes data using Pickle."""
  pickle_data = pickle.dumps(data)
  return pickle_data

def compare_encoding_sizes(data_payloads):
  """Compares the sizes of data encoded with Base64+JSON, JSON, and Pickle."""
  print(f"{'Payload':<20} {'Base64+JSON Size':<20} {'JSON Size':<15} {'Pickle Size':<15}")
  print("-" * 70)
  for payload in data_payloads:
    base64_json_encoded = encode_with_base64_and_json(payload)
    json_encoded = encode_with_json(payload)
    pickle_encoded = encode_with_pickle(payload)
    print(f"{str(payload)[:15]:<20} {len(base64_json_encoded):<20} {len(json_encoded):<15} {len(pickle_encoded):<15}")

if __name__ == "__main__":
  # Example data payloads
  data_payloads = [
    {"key": "value"},
    [1, 2, 3, 4, 5],
    "A simple string",
    1234567890,
    {"nested": {"key": "value", "list": [1, 2, 3]}},
    [True, False, None],
  ]
  compare_encoding_sizes(data_payloads)