import * as cdk from 'aws-cdk-lib'
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as apigateway from 'aws-cdk-lib/aws-apigateway'
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb'
import { pythonBundlingOptions } from './base'

export interface IIotComputeStackProps extends cdk.StackProps {
  devicesTable: dynamodb.ITable
}

export class IotComputeStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props: IIotComputeStackProps) {
    super(scope, id, props)

    const { devicesTable } = props

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
      environment: {
        DEVICES_TABLE_NAME: devicesTable.tableName,
      },
    }

    // Define a Python Lambda function for IoT message processing
    const iotProcessingFunction = new lambda.Function(this, 'process-iot-message', {
      ...defaultLambdaProps,
      handler: 'app.handle_iot_message',
    })
    devicesTable.grantFullAccess(iotProcessingFunction)

    // Add IoT Core publish permissions to the IoT processing Lambda
    iotProcessingFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['iot:Publish'],
        resources: ['arn:aws:iot:*:*:topic/*'], // Adjust the topic ARN as needed for your use case
      }),
    )

    // Create separate lambda functions for each API operation
    const registerDeviceFunction = new lambda.Function(this, 'register-device', {
      ...defaultLambdaProps,
      handler: 'app.app',
      environment: {
        ...defaultLambdaProps.environment,
        STAGE: 'prod',
      },
    })
    devicesTable.grantFullAccess(registerDeviceFunction)

    const seedDeviceFunction = new lambda.Function(this, 'seed-device', {
      ...defaultLambdaProps,
      handler: 'app.app',
      environment: {
        ...defaultLambdaProps.environment,
        STAGE: 'prod',
      },
    })
    devicesTable.grantFullAccess(seedDeviceFunction)

    // Add IoT permissions to the register device Lambda
    registerDeviceFunction.addToRolePolicy(
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

    // Create API Gateway REST API (not using proxy integration)
    const api = new apigateway.RestApi(this, 'iot-rest-api', {
      restApiName: 'IoT Device API',
      description: 'API for IoT device registration',
      deployOptions: {
        stageName: 'api',
      },
      // Enable API key
      apiKeySourceType: apigateway.ApiKeySourceType.HEADER,
      defaultCorsPreflightOptions: {
        allowHeaders: ['Authorization', 'Content-Type', 'X-Amz-Date', 'X-Amz-Security-Token', 'X-Api-Key'],
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowOrigins: ['*'],
      },
    })

    // Add resources and methods to the API
    const registerResource = api.root.addResource('register-device')
    const seedResource = api.root.addResource('seed-device')

    // Add POST method to register-device resource
    registerResource.addMethod('POST', new apigateway.LambdaIntegration(registerDeviceFunction), {
      apiKeyRequired: true, // Require API key for this method
    })

    // Add POST method to seed-device resource
    seedResource.addMethod('POST', new apigateway.LambdaIntegration(seedDeviceFunction), {
      apiKeyRequired: true, // Require API key for this method
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
