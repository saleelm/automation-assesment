.PHONY: test test-list test-setup test-local-setup test-local test-local-list \
        test-headed test-web test-mobile test-android test-auth test-smoke test-sanity \
        test-regression test-api test-e2e clean-results clean-report clean-allure \
        report report-allure report-allure-open \
        typecheck lint lint-fix format format-check lint-waits install-dev install-appium \
        appium save-session

VENV ?= .venv
BIN = $(if $(wildcard $(VENV)/bin/*),$(VENV)/bin/, )

install-dev:
	pip install -e ".[dev]"

install-appium:
	npm install
	npx appium driver list --installed 2>&1 | grep -q uiautomator2 || npx appium driver install uiautomator2

appium:
	npm exec -- appium --address 127.0.0.1 --port 4723 --allow-insecure chromedriver_autodownload

save-session:
	python3 scripts/save_session.py

test:
	pytest

test-list:
	pytest --collect-only -q

test-setup:
	pytest -m setup

test-local-setup:
	ENVIRONMENT=local pytest -m setup

test-local:
	ENVIRONMENT=local pytest

test-local-list:
	ENVIRONMENT=local pytest --collect-only -q

test-headed:
	pytest --headed

test-web:
	pytest --platform web

test-mobile:
	pytest --platform mobile-emulated

test-android:
	pytest --platform android-device

test-auth:
	pytest -m auth

test-smoke:
	pytest -m smoke

test-sanity:
	pytest -m sanity

test-regression:
	pytest -m regression

test-api:
	pytest -m api

test-e2e:
	pytest -m e2e

clean-results:
	rm -rf allure-results test-results allure-report junit-results

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
	$(BIN)mypy src tests

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
