import * as cdk from 'aws-cdk-lib'
import * as lambda from 'aws-cdk-lib/aws-lambda'
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

    const defaultLambdaProps /*: Partial<lambda.FunctionProps> */ = {
      code: assetCode,
      layers: layers,
      memorySize: 1769,
      runtime: lambda.Runtime.PYTHON_3_13,
      timeout: cdk.Duration.seconds(60),
    }

    // Define a Python Lambda function
    const pythonFunction = new lambda.Function(this, 'process-iot-message', {
      ...defaultLambdaProps,
      handler: 'app.handle_iot_message', // Specify the handler function
    })
  }
}
