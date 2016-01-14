PROJECT_ID := osmreporter

SHELL := /bin/bash

# ----------------------------------------------------------------------------
#    P R O D U C T I O N     C O M M A N D S
# ----------------------------------------------------------------------------

run:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) up -d web

build:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) build web

kill:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Killing in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) kill web

rm: kill
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Removing in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) rm web

# ----------------------------------------------------------------------------
#    D E V E L O P M E N T     C O M M A N D S
# ----------------------------------------------------------------------------

# Run pep8 style checking
#http://pypi.python.org/pypi/pep8
pep8:
	@echo
	@echo "-----------"
	@echo "PEP8 issues"
	@echo "-----------"
	@pep8 --version
	@pep8 --repeat --ignore=E203,E121,E122,E123,E124,E125,E126,E127,E128,E402 --exclude venv,pydev,fabfile.py . || true

pylint:
	@echo
	@echo "-----------------"
	@echo "Pylint violations"
	@echo "-----------------"
	@pylint --version
	@pylint --reports=n --rcfile=pylintrc reporter || true

build-test:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building in test mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) build test

run-test:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in test mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) run test

build-dev:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building in development mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) build dev


run-dev:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in development mode"
	@echo "You can access it on http://localhost:64002"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) up -d dev

log:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing flask logs in development mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) logs dev
