STACK_NAME=cloud-resume-challenge
PROFILE=my-user
FUNCTION_NAME=PutVisitorFunction
LOCAL_EVENT_FILE=events/put-event.json

deploy:
	aws-vault exec $(PROFILE) --no-session -- sam build && sam deploy --stack-name $(STACK_NAME) --capabilities CAPABILITY_IAM

invoke-put:
	aws-vault exec my-user --no-session -- sam build && \
	aws-vault exec my-user --no-session -- sam local invoke PutVisitorFunction -e events/put-event.json --env-vars env.json

invoke-get:
	sam build && sam local invoke GetVisitorFunction -e events/get-event.json --env-vars env.json
