import { aws_lambda as lambda, BundlingOptions } from 'aws-cdk-lib'

const command = [
  'bash',
  '-c',
  [
    'cd /asset-input',

    // Install poetry
    'curl -sSL https://install.python-poetry.org | python3 -',
    'export PATH=/tmp/home/.local/bin:$PATH',

    // Install deps
    'poetry install --no-root',

    // Copy .venv dependencies to output
    'mkdir /asset-output/python',
    'cp -r ./.venv/lib/python3.13/site-packages/* /asset-output/python',

    // This is packaged already in AWS lambda and makes the build too big so we delete them.
    // Also for some reason chalice always wants to install botocore.
    // Poetry does not support overrides (https://github.com/python-poetry/poetry/issues/697)
    'rm -rf /asset-output/python/boto3* /asset-output/python/botocore*',
    'ls -hal /asset-output/python',
  ].join(' && '),
]

export const pythonBundlingOptions: BundlingOptions = {
  command: command,
  environment: { HOME: '/tmp/home' },
  image: lambda.Runtime.PYTHON_3_13.bundlingImage,
}
