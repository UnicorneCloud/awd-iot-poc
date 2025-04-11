import * as cdk from 'aws-cdk-lib'
import { Construct } from 'constructs'
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb'

export interface IDynamoDbStackProps extends cdk.StackProps {
  tableNamePrefix?: string
}

export class DynamoDbStack extends cdk.Stack {
  public readonly devicesTable: dynamodb.ITable

  constructor(scope: Construct, id: string, props?: IDynamoDbStackProps) {
    super(scope, id, props)

    const tableNamePrefix = props?.tableNamePrefix || ''

    // Create the DynamoDB table for IoT devices
    this.devicesTable = new dynamodb.Table(this, 'IoTDevicesTable', {
      tableName: `${tableNamePrefix}IoTDevices`,
      partitionKey: {
        name: 'device_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Change to RETAIN for production
    })

    // Add tags
    cdk.Tags.of(this.devicesTable).add('Project', 'IoTDeviceManagement')
  }
}
