#!/usr/bin/env node
import 'source-map-support/register'
import * as cdk from 'aws-cdk-lib'
import { DynamoDbStack, IotComputeStack, IoTCoreStack } from '../lib'

const app = new cdk.App()
const rawEnvName = app.node.tryGetContext('envName')
if (!rawEnvName) {
  throw new Error('Error, you have to add context: envName')
}

// Create DynamoDB stack for device data storage
const dynamoDbStack = new DynamoDbStack(app, 'IotPocDynamoDbStack', {
  tableNamePrefix: 'IotPoc-',
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
})

// Create the IoT Compute stack with access to the DynamoDB table
const computeStack = new IotComputeStack(app, 'IotComputeStack', {
  devicesTable: dynamoDbStack.devicesTable,
})

new IoTCoreStack(app, 'IotCoreStack', {
  rawDataProcessingLambda: computeStack.iotProcessingFunction,
})
