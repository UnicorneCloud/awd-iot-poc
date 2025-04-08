from chalice import Chalice
import pickle
import logging

app = Chalice(app_name='iot-poc')

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

@app.lambda_function()
def handle_iot_message(event, context):
  """
  AWS Lambda function to process a pickled Python serialization from an IoT message.
  """
  try:
    # Assume the pickled data is passed in the event body
    pickled_data = event.get('body')
    if not pickled_data:
      logger.error("No pickled data found in the event body.")
      return {
        'statusCode': 400,
        'body': 'No pickled data provided.'
      }

    # Deserialize the pickled data
    deserialized_data = pickle.loads(bytes(pickled_data, 'utf-8'))
    logger.info("Deserialized data: %s", deserialized_data)

    return {
      'statusCode': 200,
      'body': 'Message processed successfully.'
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
