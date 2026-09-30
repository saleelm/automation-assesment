---
name: test-authoring
description: Step-by-step workflow for authoring new automated tests from user prompts
---
# Test Authoring Workflow

When asked to add a new test case:
1. Identify the target feature and page in `src/ui_test_platform/pages/<app>/`.
2. Inspect or discover the DOM elements on both Desktop and Mobile viewports.
3. If new elements or actions are required:
   - Add them to the corresponding Page Object in `src/ui_test_platform/pages/<app>/<page>.py`.
   - Ensure the fixture is registered in `src/ui_test_platform/fixtures/pom/page_object_fixtures.py`.
4. Create or append the test in `tests/<feature>/test_<feature>.py`:
   - Group inside a descriptive `class Test<Feature>:`.
   - Decorate with `@tags(Tag.<SCOPE>, Tag.<MODULE>)`.
   - Decorate with `@title("TC## should <verb> <subject> when <condition>")`.
   - Group actions into BDD steps: `with step("Given..."):`, `When`, `Then`.
   - Import symbols ONLY from `ui_test_platform.fixtures.pom.test_options`.
5. Run `make lint` and `make typecheck`.
6. Run the test with `pytest --platform web` and `pytest --platform mobile-emulated`.
