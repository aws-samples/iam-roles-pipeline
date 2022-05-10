import boto3
import json
import os
import copy


s3 = boto3.client('s3')


def handler(event, context):
    """
    Lambda entry point.
    CloudFormation Macro implementation for creating IAM Roles.
    This handler is called by CloudFormation service during the deployment command, in the tranformation phase.
    It will include the roles and policies that were uploaded to s3://<BUCKET_ROLES>/.
    """
    return {
        'requestId': event['requestId'],
        'status': 'success',
        'fragment': convert_template(event['fragment']),
    }


# Bucket where it is stored the policies and roles definitions
bucket_roles = os.environ['BUCKET_ROLES']


def convert_template(fragment):
    """
    Converts original template (s3://<BUCKET_ROLES>/cloudformation/roles-template.yml) into a template with the requested user roles.
    Include, in the cloudformation template, AWS::IAM::Role resources for each role defined in s3://<BUCKET_ROLES>/roles.json
    """
    # Debug input
    print('This was the fragment: {}'.format(fragment))

    resources = fragment['Resources']
    # Process roles
    roles = get_object_as_json('roles.json')
    for name, role_obj in roles.items():
        role_cf = {
            'Type': 'AWS::IAM::Role',
            'Properties': {
                'AssumeRolePolicyDocument': build_assume_role_policy(role_obj),
                'Path': role_obj.get('Path', '/'),
                'Policies': load_policies_content(role_obj['Policies'])
            }
        }
        if os.environ.get('PERMISSIONS_BOUNDARY_ROLE_ARN'):
            role_cf['Properties']['PermissionsBoundary'] = os.environ.get(
                'PERMISSIONS_BOUNDARY_ROLE_ARN')
        resource_name = sanitize_resource_name(name)
        resources[resource_name] = role_cf

    # Debug output
    print('This is the transformed fragment: {}'.format(fragment))
    # Return the converted/expanded template fragment
    return fragment


def build_assume_role_policy(role_obj):
    assume_role = copy.deepcopy(ASSUME_ROLE_POLICY_OBJ)
    assume_role['Statement'][0]['Principal']['Service'] = role_obj['Service']
    return assume_role


def sanitize_resource_name(name):
    """
    Each AWS::IAM::Role resource name will have the same name from roles.json file.
    Cloudformation doesn't allow dash character '-', so replace '-' with 'Dash'. 
    """
    return f'{name.replace("-", "Dash")}Resource'


def get_object_as_json(key_name):
    """
    Reads text files from S3 and converts to json object (python dict)
    """
    s3_object = s3.get_object(Bucket=bucket_roles, Key=key_name)
    body = s3_object['Body']
    return json.loads(body.read())


def get_policy_name_from_file(file_name):
    """
    Inline policy name will have the same name of file stored in the bucket.
    Remove file extension to build the policy name.
    """
    return file_name.split('/')[-1].split('.')[0]


def load_policies_content(policy_files):
    "Generates inline policy document that will be attached to the roles"
    return [
        {'PolicyName': get_policy_name_from_file(policy_file),
         'PolicyDocument': get_object_as_json(policy_file)} for policy_file in policy_files]


ASSUME_ROLE_POLICY_OBJ = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    # Parameterized by user
                ]
            },
            "Action": [
                "sts:AssumeRole"
            ]
        }
    ]
}
