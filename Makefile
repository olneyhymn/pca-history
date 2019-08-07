all: deploy

.PHONY: deploy
deploy:
	STATIC_DEPS=true pip3 install -U twitter requests git+https://github.com/mobolic/facebook-sdk.git#egg=facebook-sdk -t .
	serverless deploy

.PHONY: clean
clean:
	git clean -fd
