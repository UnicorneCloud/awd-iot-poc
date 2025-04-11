import * as cdk from 'aws-cdk-lib'
import * as iot from 'aws-cdk-lib/aws-iot'
import * as logs from 'aws-cdk-lib/aws-logs'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as lambda from 'aws-cdk-lib/aws-lambda'

interface IIoTCoreStackProps extends cdk.StackProps {
  rawDataProcessingLambda: lambda.IFunction
}

export class IoTCoreStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props: IIoTCoreStackProps) {
    super(scope, id, props)

    // Create CloudWatch Log Groups for rule actions and error logging
    const rawDataLogGroup = new logs.LogGroup(this, 'RawDataLogGroup', {
      logGroupName: '/aws/iot/rawDataRule',
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    })

    const processedDataLogGroup = new logs.LogGroup(this, 'ProcessedDataLogGroup', {
      logGroupName: '/aws/iot/processedDataRule',
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    })

    // Create error logging destinations
    const rawDataErrorLogGroup = new logs.LogGroup(this, 'RawDataErrorLogGroup', {
      logGroupName: '/aws/iot/rawDataRule/errors',
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    })

    const processedDataErrorLogGroup = new logs.LogGroup(this, 'ProcessedDataErrorLogGroup', {
      logGroupName: '/aws/iot/processedDataRule/errors',
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    })

    // Create the raw_data rule
    const rawDataRule = new iot.CfnTopicRule(this, 'RawDataRule', {
      ruleName: 'raw_data',
      topicRulePayload: {
        // eslint-disable-next-line quotes
        sql: "SELECT encode(*, 'base64') AS data FROM 'temperatures'",
        actions: [
          // Lambda action
          {
            lambda: {
              functionArn: props.rawDataProcessingLambda.functionArn,
            },
          },
          // CloudWatch Logs action
          {
            cloudwatchLogs: {
              logGroupName: rawDataLogGroup.logGroupName,
              roleArn: this.createLogsRole('RawDataLogsRole').roleArn,
            },
          },
        ],
        errorAction: {
          cloudwatchLogs: {
            logGroupName: rawDataErrorLogGroup.logGroupName,
            roleArn: this.createLogsRole('RawDataErrorLogsRole').roleArn,
          },
        },
        description: 'Rule for processing raw device data',
        awsIotSqlVersion: '2016-03-23',
      },
    })

    // Create the data_processed rule
    const processedDataRule = new iot.CfnTopicRule(this, 'ProcessedDataRule', {
      ruleName: 'data_processed',
      topicRulePayload: {
        // eslint-disable-next-line quotes
        sql: "SELECT * FROM 'temperatures/json'",
        actions: [
          // CloudWatch Logs action only
          {
            cloudwatchLogs: {
              logGroupName: processedDataLogGroup.logGroupName,
              roleArn: this.createLogsRole('ProcessedDataLogsRole').roleArn,
            },
          },
        ],
        errorAction: {
          cloudwatchLogs: {
            logGroupName: processedDataErrorLogGroup.logGroupName,
            roleArn: this.createLogsRole('ProcessedDataErrorLogsRole').roleArn,
          },
        },
        description: 'Rule for logging processed device data',
        awsIotSqlVersion: '2016-03-23',
      },
    })

    // Grant the raw_data rule permission to invoke the Lambda function
    props.rawDataProcessingLambda.grantInvoke(
      new iam.ServicePrincipal('iot.amazonaws.com', {
        conditions: {
          ArnLike: {
            'aws:SourceArn': `arn:aws:iot:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/${rawDataRule.ruleName}`,
          },
        },
      }),
    )
  }

  // Helper method to create IAM roles for CloudWatch Logs actions
  private createLogsRole(id: string): iam.Role {
    const role = new iam.Role(this, id, {
      assumedBy: new iam.ServicePrincipal('iot.amazonaws.com'),
    })

    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['logs:CreateLogStream', 'logs:PutLogEvents', 'logs:DescribeLogStreams'],
        resources: ['*'],
      }),
    )

    return role
  }
}
