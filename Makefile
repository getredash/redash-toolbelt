.DEFAULT_GOAL := help

## cleanup build artifacts
clean:
	rm -rf cover .coverage cover.xml .tox/ nosetests* dist build *.egg-info
	find . -name "*.pyc" -print0 | xargs -0 rm

## clean up everything (including git cleanup)
dist-clean: clean
	git clean -d --force -X

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

