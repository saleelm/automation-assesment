.PHONY: test test-list test-setup test-local-setup test-local test-local-list \
        test-headed test-web test-mobile test-android test-auth test-game test-smoke test-sanity \
        test-regression test-api test-e2e clean-results clean-report clean-allure \
        report report-allure report-allure-open \
        typecheck lint lint-fix format format-check lint-waits install-dev install-appium \
        appium save-session

VENV ?= .venv
BIN = $(if $(wildcard $(VENV)/bin/*),$(VENV)/bin/, )
PYTEST ?= $(BIN)pytest

install-dev:
	pip install -e ".[dev]"

install-appium:
	npm install
	npx appium driver list --installed 2>&1 | grep -q uiautomator2 || npx appium driver install uiautomator2

appium:
	npm exec -- appium --address 127.0.0.1 --port 4723 --allow-insecure chromedriver_autodownload

save-session:
	python3 scripts/save_session.py

save-game-session:
	python3 scripts/save_session.py --game --persistent

test:
	$(PYTEST)

test-list:
	$(PYTEST) --collect-only -q

test-setup:
	$(PYTEST) -m setup

test-local-setup:
	ENVIRONMENT=local $(PYTEST) -m setup

test-local:
	ENVIRONMENT=local $(PYTEST)

test-local-list:
	ENVIRONMENT=local $(PYTEST) --collect-only -q

test-headed:
	$(PYTEST) --headed

test-web:
	$(PYTEST) --platform web

test-mobile:
	$(PYTEST) --platform mobile-emulated

test-android:
	$(PYTEST) --platform android-device

test-auth:
	$(PYTEST) -m auth

test-game:
	$(PYTEST) -m game

test-smoke:
	$(PYTEST) -m smoke

test-sanity:
	$(PYTEST) -m sanity

test-regression:
	$(PYTEST) -m regression

test-api:
	$(PYTEST) -m api

test-e2e:
	$(PYTEST) -m e2e

clean-results:
	rm -rf allure-results test-results allure-report junit-results videos

clean-report:
	rm -rf allure-report

clean-allure:
	rm -rf allure-results allure-report

report:
	allure serve allure-results

report-allure:
	allure generate allure-results --clean -o allure-report

report-allure-open:
	allure open allure-report

typecheck:
	$(BIN)mypy src tests conftest.py

lint:
	$(BIN)ruff check . && $(MAKE) lint-waits

lint-fix:
	$(BIN)ruff check . --fix

format:
	$(BIN)ruff format .

format-check:
	$(BIN)ruff format --check .

lint-waits:
	! grep -rnE --exclude-dir=__pycache__ --include="*.py" "wait_for_timeout|time\.sleep" src tests
