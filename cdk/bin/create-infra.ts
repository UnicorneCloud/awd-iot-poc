#!/usr/bin/env node
import 'source-map-support/register'
import * as cdk from 'aws-cdk-lib'
import { IotComputeStack } from '../lib'

const app = new cdk.App()
const rawEnvName = app.node.tryGetContext('envName')
if (!rawEnvName) {
  throw new Error('Error, you have to add context: envName')
}

new IotComputeStack(app, 'IotComputeStack', {})
