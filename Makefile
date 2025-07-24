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

integration-test:
	@echo "🔍 Running integration test for visitor counter..."
	@DOMAIN_NAME=$$(cat config.json | jq -r '.DOMAIN_NAME'); \
	FIRST=$$(curl -s https://$$DOMAIN_NAME/visitors | jq '.count | tonumber'); \
	curl -s -X PUT -H "Content-Type: application/json" -d '{}' https://$$DOMAIN_NAME/visitors > /dev/null; \
	SECOND=$$(curl -s https://$$DOMAIN_NAME/visitors | jq '.count | tonumber'); \
	echo "First Count: $$FIRST"; \
	echo "Second Count: $$SECOND"; \
	if [ $$FIRST -lt $$SECOND ]; then \
		echo "✅ PASS: Counter incremented successfully."; \
	else \
		echo "❌ FAIL: Counter did not increment."; \
		exit 1; \
	fi

