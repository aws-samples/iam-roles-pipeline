#!/bin/sh

aws cloudformation deploy \
    --template-file pipeline-template.packaged.template \
    --stack-name RolesPipelineStack \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM