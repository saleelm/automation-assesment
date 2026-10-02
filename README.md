# Stumble Guys Automation Platform (`ui-test-platform`)

> **QA Automation Lead Assessment Submission for Mirai (a Scopely Company)**  
> **Author:** Candidate  
> **Target Portal:** [Stumble Guys Web Game Portal](https://www.stumbleguys.com/)

[![CI](https://github.com/example/stumbleguys-automation/actions/workflows/sanity.yml/badge.svg)](https://github.com/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Sync%20API-green.svg)](https://playwright.dev/python/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-black.svg)](https://github.com/astral-sh/ruff)
[![Type Checked](https://img.shields.io/badge/Type%20Check-Mypy%20Strict-blueviolet.svg)](https://mypy-lang.org/)

---

## 1. Executive Summary & Architectural Vision

This repository presents **`ui-test-platform`**, an enterprise-grade UI automation framework engineered for modern web game portals, cross-platform responsiveness, and AI-assisted test authoring. 

Rather than a collection of ad-hoc test scripts, this platform demonstrates **QA Automation Lead architecture**:
- **Cross-Platform by Default:** A unified test suite runs seamlessly across **Desktop Web** (`--platform web`), **Mobile Web Emulation** (`--platform mobile-emulated`), and **Real Android Devices** (`--platform android-device`).
- **Strict Architectural Boundaries:** Enforced by Ruff `TID251` (tests can only import testing symbols from `ui_test_platform.fixtures.pom.test_options`).
- **Zero-Flakiness Policy:** Enforced by custom linter `make lint-waits` which strictly bans arbitrary `time.sleep` and `wait_for_timeout` across the entire codebase.
- **Bonus WebGL Canvas Game Automation:** Comprehensive strategy tackling the `/play` Unity WebGL canvas through container lifecycle evaluation, canvas context introspection, and viewport input dispatch.
- **Natural Language Test Authoring:** Integrated Cursor/Antigravity Rules (`.cursor/rules/`) and Skills (`.cursor/skills/`) enabling engineers and AI agents to reliably scaffold and append new tests purely from conversational prompts.

---

## 2. Test Coverage & Assessment Scenarios

| Area | Feature | Test Identifier | Platforms | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Authentication** | Login Navigation & Trigger | `test_tc01_should_open_login_triggers_and_render_options` | Desktop + Mobile | Opens header avatar menu, triggers login dialog, and asserts login button rendering. |
| **Authentication** | Negative Form Validation | `test_tc02_should_validate_invalid_email_format` | Desktop + Mobile | Submits malformed credentials and asserts application stability without crashing. |
| **Authentication** | ID Provider Flow Integration | `test_tc03_should_automate_email_otp_retrieval_and_entry` | Desktop + Mobile | Provisions automated inbox, initiates login pipeline, and verifies Scopely ID prompt. |
| **Authentication** | Account Signup & Email Verify | `test_tc04_should_automate_new_account_signup_and_email_verification` | Desktop + Mobile | Provisions API mailbox, submits signup agreement, polls inbox, and verifies received confirmation link. |
| **Authentication** | End-to-End Signup & OTP Login | `test_tc05_should_complete_end_to_end_signup_and_otp_login` | Desktop + Mobile | **Full E2E Auth:** Mailbox creation $\to$ signup $\to$ email confirmation $\to$ OTP retrieval $\to$ OTP submission $\to$ portal redirection & cookie dismissal. |
| **Shop** | Catalog & Identity | `test_tc01_should_display_special_deals_and_validate_username` | Desktop + Mobile | Browses shop catalog, verifies special deals hero, and validates player username. |
| **Shop** | Safe Purchase Flow | `test_tc02_should_safely_cancel_purchase_flow_before_confirmation` | Desktop + Mobile | **Mandatory Assessment Requirement:** Selects offer, opens checkout dialog, and safely cancels before payment entry. |
| **WebGL Game (Bonus)** | Canvas Runtime Init | `test_tc01_should_initialize_webgl_game_container` | Desktop | Navigates to `/play`, asserts `#player` container mount, evaluates WebGL2/WebGL context. |
| **WebGL Game (Bonus)** | Canvas Viewport Input | `test_tc02_should_dispatch_canvas_viewport_interactions` | Desktop | Computes canvas bounding box, clicks viewport center, and dispatches navigation keys. |

### 🔑 Automated Disposable Email & OTP Pipeline (`TempMailClient`)
The authentication suite eliminates flaky hardcoded credentials and manual 2FA interventions by integrating an automated API-driven disposable mailbox service:
- **Zero Credentials Flake:** Dynamically provisions fresh isolated inboxes (`@uberip.com` / `mail.tm` API) per test run.
- **Link & OTP Extraction:** Asynchronously polls the automated inbox, parses HTML and text bodies to extract magic verification links and 6-digit Scopely ID OTP codes via regex.
- **Rate-Limit Resilient:** Gracefully detects public mail service rate-limits (`MailServiceRateLimitError`) to avoid false test failures.

---

## 3. Technology Stack

- **Core Engine:** Python (3.11+) + Playwright (Sync API)
- **Test Runner:** Pytest 8+, `pytest-playwright`, `pytest-xdist` (parallel execution with `filelock`), `pytest-split`
- **Linting & Formatting:** Ruff (strict linting, ban imports rule, formatting)
- **Type Safety:** Mypy (`strict = true`, no implicit `Any`, full type annotations)
- **Reporting:** Allure Framework (`allure-pytest`) with step-level BDD reporting and failure attachments
- **CI/CD:** GitHub Actions Matrix (`on-demand.yml`, `sanity.yml`)
- **Containerization:** Docker (`Dockerfile`)

---

## 4. Quick Start & Execution

### Prerequisites
- Python 3.11+
- Virtual environment (`venv` or `poetry`)

### Setup
```bash
# Clone the repository
git clone https://github.com/example/stumbleguys-automation.git
cd stumbleguys-automation

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies in editable mode
make install-dev

# Install Playwright browser binaries
playwright install chromium
```

### Running Tests

```bash
# 1. Desktop Web (Default)
make test-web
# or: pytest --platform web

# 2. Mobile Web Emulation (Pixel 7 / iPhone viewport & touch)
make test-mobile
# or: pytest --platform mobile-emulated

# 3. Specific Feature Suites
make test-auth         # Run login tests
pytest -m shop         # Run shop & safe purchase tests
pytest -m webgl        # Run WebGL canvas bonus tests

# 4. Static Analysis & Flakiness Verification
make lint              # Verifies Ruff + bans time.sleep / wait_for_timeout
make typecheck         # Verifies mypy --strict
make format-check      # Verifies PEP8 formatting
```

### Generating Allure Reports
```bash
# Generate and open interactive Allure report
make report-allure
make report-allure-open
```

---

## 5. Bonus Challenge: WebGL Game Canvas Automation

### The Problem
Traditional test automation frameworks (Selenium, Cypress, standard Playwright locators) can only interact with standard DOM elements. A WebGL game renders inside a `<canvas>` element as pixel buffers, making internal buttons and stumblers invisible to DOM locators.

### The Lead-Grade Solution
This framework implements a **three-tier automation strategy**:
1. **Container & WebGL Context Validation:** Injects JavaScript to verify WebGL context availability (`webgl2` / `webgl`) and checks Unity loader lifecycle events.
2. **Coordinate & Viewport Input Dispatch:** Computes runtime bounding boxes of the `#player` canvas and dispatches proportional mouse clicks (`mouse.click(x, y)`) and keyboard event sequences (`Space`, `ArrowRight`, `ArrowLeft`).
3. **Perceptual Visual Regression (Optional Expansion):** Visual snapshot diffing against baseline renders to catch graphical anomalies.

---

## 6. Authoring Tests with Plain-English Prompts (AI-Augmented QA)

The repository includes `.cursor/rules/` and `.cursor/skills/`. Any AI coding assistant (Antigravity, Cursor, Copilot) can author new tests directly from prompts such as:

> *"Add a test case: User selects an offer and validates that the price tag matches USD currency format."*

The assistant automatically:
1. Discovers the DOM element across desktop and mobile viewports.
2. Extends `ShopPage` in `src/ui_test_platform/pages/stumbleguys/shop_page.py`.
3. Injects the test under `tests/shop/` importing exclusively from `test_options.py`.
4. Runs `make lint` and `make typecheck` to ensure zero compilation or styling errors.

---

## 7. Assumptions & Limitations

1. **Authentication Mode:** The Stumble Guys web portal uses dynamic OAuth/Scopely ID modal interactions and Usercentrics CMP cookie banners. The framework includes proactive banner dismissal and negative credential validation flows.
2. **Safe Purchase Constraint:** In strict adherence to assessment rules, all purchase flows terminate before payment confirmation or submission of credit card details.
3. **Real Device Execution:** `--platform android-device` utilizes Playwright's native Android adb bridge. In CI environments without physical hardware attached, `--platform mobile-emulated` is used for 100% deterministic mobile browser testing.
