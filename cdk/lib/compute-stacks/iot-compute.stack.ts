import * as cdk from 'aws-cdk-lib'
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as apigateway from 'aws-cdk-lib/aws-apigateway'
import * as path from 'path'
import { pythonBundlingOptions } from './base'

export class IotComputeStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    const lambdaPythonVendorsLayer = new lambda.LayerVersion(this, 'iot-poc-python-vendors', {
      code: lambda.Code.fromAsset('../src', {
        bundling: pythonBundlingOptions,
        exclude: ['*', '!pyproject.toml', '!poetry.lock'],
      }),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_13],
    })

    // Create lambda
    const assetCode = lambda.Code.fromAsset('../src', {
      exclude: ['.venv', 'perm_files', 'vendors', 'requirements.txt', '*.pyc', '.pytest_cache', '.chalice'],
    })

    const layers: Array<lambda.ILayerVersion> = [lambdaPythonVendorsLayer]

    const defaultLambdaProps = {
      code: assetCode,
      layers: layers,
      memorySize: 1769,
      runtime: lambda.Runtime.PYTHON_3_13,
      timeout: cdk.Duration.seconds(60),
    }

    // Define a Python Lambda function
    const iotProcessingFunction = new lambda.Function(this, 'process-iot-message', {
      ...defaultLambdaProps,
      handler: 'app.handle_iot_message', // Specify the handler function
    })

    // Create the API Lambda function
    const apiFunction = new lambda.Function(this, 'iot-api', {
      ...defaultLambdaProps,
      handler: 'app.app', // Chalice app handler
      environment: {
        STAGE: 'prod', // Chalice environment variable
      },
    })

    // Add IoT permissions to the API Lambda
    apiFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'iot:CreateThing',
          'iot:DescribeThing',
          'iot:CreateKeysAndCertificate',
          'iot:AttachThingPrincipal',
          'iot:CreatePolicy',
          'iot:AttachPolicy',
          'iot:DescribeEndpoint',
        ],
        resources: ['*'], // In production, you should scope this down
      }),
    )

    // Create API Gateway REST API with API key required
    const api = new apigateway.LambdaRestApi(this, 'iot-rest-api', {
      handler: apiFunction,
      proxy: true,
      deployOptions: {
        stageName: 'api',
      },
      description: 'API for IoT device registration',
      apiKeySourceType: apigateway.ApiKeySourceType.HEADER, // API key will be provided in the header
    })

    // Create API key
    const apiKey = new apigateway.ApiKey(this, 'iot-api-key', {
      apiKeyName: 'iot-device-registration-key',
      description: 'API Key for IoT device registration API',
      enabled: true,
    })

    // Create usage plan and associate it with the API and API key
    const usagePlan = new apigateway.UsagePlan(this, 'iot-usage-plan', {
      name: 'iot-api-usage-plan',
      description: 'Usage plan for IoT API',
      apiStages: [
        {
          api: api,
          stage: api.deploymentStage,
        },
      ],
      // Optional: Set quota and throttling limits
      quota: {
        limit: 1000,
        period: apigateway.Period.MONTH,
      },
      throttle: {
        rateLimit: 10,
        burstLimit: 20,
      },
    })

    // Associate the API key with the usage plan
    usagePlan.addApiKey(apiKey)
  }
}
