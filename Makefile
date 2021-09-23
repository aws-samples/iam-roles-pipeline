.PHONY: package deploy destroy

# default target, when make is executed without arguments: it tries to deploy pipeline stack
all: deploy

deploy:
ifdef bucket
	./scripts/package.sh ${bucket}
	./scripts/deploy-macro.sh
else
	@echo 'no bucket parameter defined'
	@echo 'Usage:'
	@echo 'make deploy bucket=<bucket-name-for-deploying-pipeline-cf-template>'
endif

# Destroy all
destroy:
	@echo 'You must empty buckets whose name starts with "rolespipelinestack-" before proceeding with the destroy command'
	@echo -n "Proceed destroy? [y/N] " && read ans && [ $${ans:-N} = y ]
	@echo 'You must delete CloudFormation RolesStack before proceeding with the destroy command'
	@echo -n "Proceed destroy? [y/N] " && read ans && [ $${ans:-N} = y ]
	./scripts/delete-stack.sh
