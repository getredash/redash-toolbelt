.DEFAULT_GOAL := help

## run all tests dockerized on all configured environments
check: redash-start
	docker container run --mount src=${PWD},target=/src,type=bind -i -t --rm sawkita/tox:all /bin/bash -c "cd /src && tox"

## cleanup build artifacts
clean:
	rm -rf cover .coverage cover.xml .tox/ nosetests* dist build *.egg-info
	find . -name "*.pyc" -print0 | xargs -0 rm

## clean up everything (including git cleanup)
dist-clean: clean
	git clean -d --force -X

## stop and cleanup redash orchestration and repository
redash-purge:
	cd redash && docker-compose down || exit 0
	cd redash && docker-compose rm -f || exit 0
	cd redash && rm -rf postgres-data || exit 0

redash-prepare: redash-purge
	cd redash && tar xjf postgres-data.tar.bz2

## start redash orchestration
redash-start: redash-prepare
	cd redash && docker-compose up -d || exit 0
	cd redash && ../misc/waitUntilReady.sh

## update cli reference README.md
cli-update-reference-manual:
	misc/createOverallHelp.sh >redash_toolbelt/cli/README.md

## Show this help screen
help:
	@printf "Available targets\n\n"
	@awk '/^[a-zA-Z\-0-9]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "%-35s %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)

