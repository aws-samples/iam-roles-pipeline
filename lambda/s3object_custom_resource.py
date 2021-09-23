from urllib.request import build_opener, HTTPHandler, Request
import boto3
import json
from zipfile import ZipFile

s3_client = boto3.client('s3')

def handler(event, context):
    """
    Lambda entry point.
    CloudFormation Custom Resource that uploads a file to a S3 bucket.
    Custom Resource parameters:
        Target:  # Target bucket where a object will be uploaded
            Bucket: 
            Key: cloudformation/roles-template.zip
        ZipBody: # Wheather the file content should be zipped
        Body: # File content that will be uploaded
    """
    print('Received request:', json.dumps(event, indent=4))

    request = event['RequestType']
    properties = event['ResourceProperties']

    if not {'Target', 'Body'}.issubset(properties.keys()):
        return send_response(event, context, 'FAILED', 'Missing required parameters')

    target = properties['Target']
    try:
        if request in {'Create', 'Update'}:
            if 'Body' in properties:
                target['Body'] = properties['Body']
                if 'ZipBody' in properties.keys():
                    print('Zip Body before put into S3')
                    with ZipFile('/tmp/body.zip','w') as zip:
                        zip.writestr(target['Key'].replace('.zip', '.yml'), properties['Body'])
                    with open('/tmp/body.zip', 'rb') as zipfile:
                        target['Body'] = zipfile.read()
                s3_client.put_object(**target)
            else:
                return send_response(event, context, 'FAILED', 'Malformed body')

            return send_response(event, context, 'SUCCESS', 'Created')

        if request == 'Delete':
            s3_client.delete_object(
                Bucket=target['Bucket'],
                Key=target['Key'],
            )
            return send_response(event, context, 'SUCCESS', 'Deleted')
    except Exception as ex:
        return send_response(event, context, 'FAILED', str(ex.args))

    return send_response(event, context, 'FAILED', f'Unexpected: {request}')


def send_response(event, context, status, message):
    """
    Sends a response to CloudFormation service, confirming whether the file upload works or not.
    """
    bucket = event['ResourceProperties'].get('Target', {}).get('Bucket')
    key = event['ResourceProperties'].get('Target', {}).get('Key')

    body = json.dumps(
        {
            'Status': status,
            'Reason': message,
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId'],
            'PhysicalResourceId': f's3://{bucket}/{key}',
            'Data': {
                'Bucket': bucket,
                'Key': key,
            },
        }
    )

    request = Request(event['ResponseURL'], data=body.encode('utf-8'), method='PUT')
    request.add_header('Content-Type', '')
    request.add_header('Content-Length', len(body))

    opener = build_opener(HTTPHandler)
    opener.open(request)