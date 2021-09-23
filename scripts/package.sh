#!/bin/sh
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 DeploymentBucketName" >&2
  exit 1
fi

bucketName=$1

aws cloudformation package \
    --template-file pipeline-template.yml \
    --s3-bucket $bucketName \
    --output-template-file pipeline-template.packaged.template