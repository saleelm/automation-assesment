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

- **Core Engine:** Python (3.11+) + Playwright (Sync API) + Appium 2 (real Android Chrome via CDP attach)
- **Test Runner:** Pytest 8+, `pytest-playwright`, `pytest-xdist` (parallel execution with `filelock`), `pytest-split`
- **Linting & Formatting:** Ruff (strict linting, ban imports rule, formatting)
- **Type Safety:** Mypy (`strict = true`, no implicit `Any`, full type annotations)
- **Reporting:** Allure Framework (`allure-pytest`) with step-level BDD reporting and failure attachments
- **CI/CD:** GitHub Actions (`on-demand.yml`, `sanity.yml` targeting Desktop Web)
- **Containerization:** Docker (`Dockerfile`)

---

## 4. Step-by-Step Setup & Execution Guide

Follow these sequential steps to set up, configure, and run tests locally or on real devices.

### Step 1: Prerequisites

Make sure the following tools are installed on your machine:
- **Python 3.11+** (`python3 --version`)
- **Node.js 18+ & npm** (required only for Appium/Android execution: `node -v`, `npm -v`)
- **Android SDK & `adb`** (required only for real Android execution: `adb version`)
- **Allure CLI** (optional for viewing HTML reports: `brew install allure` or `npm install -g allure-commandline`)

---

### Step 2: Clone the Repository & Create Virtual Environment

```bash
# 1. Clone repository
git clone git@github.com:saleelm/automation-assesment.git
cd automation-assesment

# 2. Create Python virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
# On macOS / Linux:
source .venv/bin/activate
# On Windows PowerShell:
# .venv\Scripts\Activate.ps1
```

---

### Step 3: Install Python Dependencies & Playwright Browsers

```bash
# 1. Install project dependencies in editable mode
make install-dev
# or: pip install -e ".[dev]"

# 2. Install Playwright Chromium browser binary
playwright install chromium
```

---

### Step 4: (Optional) Install and Setup ADB & Android SDK
 
To run tests against real Android devices or Android emulators (`--platform android-device`), `adb` (Android Debug Bridge) is required.

#### Option A: Quick Install via Homebrew (macOS)
```bash
brew install android-platform-tools
```

#### Option B: Via Android Studio SDK (macOS / Linux / Windows)
If Android Studio is already installed, add the platform-tools directory to your shell PATH:

- **macOS (`~/.zshrc`):**
  ```bash
  export ANDROID_HOME=$HOME/Library/Android/sdk
  export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
  ```
  Apply changes:
  ```bash
  source ~/.zshrc
  ```

- **Linux (`~/.bashrc`):**
  ```bash
  export ANDROID_HOME=$HOME/Android/Sdk
  export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
  ```
  Apply changes:
  ```bash
  source ~/.bashrc
  ```

#### Verify ADB Installation:
```bash
adb version
```

---

### Step 5: (Optional) Setup Appium 2 & Start Device / Emulator

1. **Install Appium 2 & UiAutomator2 driver:**
   ```bash
   make install-appium
   ```

2. **Connect a Real Android Device OR Start an Android Emulator:**
   - **Real Device:**
     - Enable **Developer Options** and **USB Debugging** on the phone.
     - Connect via USB and confirm the RSA authorization prompt.
   - **Android Emulator:**
     - List available AVDs:
       ```bash
       emulator -list-avds
       ```
     - Start emulator (e.g., `Medium_Phone`):
       ```bash
       emulator -avd Medium_Phone &
       ```

3. **Verify Device/Emulator is Detected by ADB:**
   ```bash
   adb devices
   ```
   *(Ensure the output lists your device/emulator with status `device`, e.g., `emulator-5554 device` or `<serial> device`).*

4. Ensure Google Chrome is installed and up-to-date on the device/emulator.

---

### Step 6: Running Tests

You can run the suite across different platforms and granular test tags:

#### 1. Desktop Web (Default)
```bash
# Using Makefile shortcut:
make test-web

# Or directly with pytest:
pytest --platform web
```

#### 2. Mobile Web Emulation (Pixel 7 / iPhone Viewport & Touch Events)
```bash
# Using Makefile shortcut:
make test-mobile

# Or directly with pytest:
pytest --platform mobile-emulated
```

#### 3. Real Android Device via Appium + CDP Attach
```bash
# Ensure Appium server is running (or pytest will auto-spawn it)
make appium

# In another terminal (with .venv activated):
make test-android
# Or specify explicit device UDID and Appium port:
# ANDROID_SERIAL=<device_udid> APPIUM_PORT=4723 pytest --platform android-device
```

#### 4. Run by Feature Marker / Tag
```bash
# Authentication tests
make test-auth
# or: pytest -m auth

# Shop & Safe Purchase tests
pytest -m shop

# WebGL Game Canvas tests
pytest -m webgl

# Smoke suite
make test-smoke

# Sanity suite
make test-sanity
```

#### 5. Headed Mode (Watch Browser Execution)
```bash
pytest --platform web --headed
```

---

### Step 7: Code Quality & Static Analysis Gates

Run quality verification to ensure linting, zero-wait policies, and strict types pass:

```bash
# 1. Run Ruff linter and zero-wait enforcement (bans time.sleep and wait_for_timeout)
make lint

# 2. Run Mypy strict type checking
make typecheck

# 3. Check code formatting
make format-check

# 4. Auto-format code
make format
```

---

### Step 8: Generating and Viewing Allure Reports

After running tests with `--alluredir=allure-results`:

```bash
# Generate static HTML report
make report-allure

# Open interactive Allure report in your default browser
make report-allure-open

# Or serve live directly from test results
make report
```

---

### Step 9: Running in Docker

Run the entire suite in a reproducible headless container:

```bash
# Build Docker image
docker build -t ui-test-platform .

# Run test suite inside container
docker run --rm -v $(pwd)/allure-results:/app/allure-results ui-test-platform
```

---

### Step 10: CI/CD Pipeline (GitHub Actions)

The CI/CD pipeline runs on GitHub Actions:
- **Sanity Workflow (`.github/workflows/sanity.yml`):** Automatically triggered on every Push, PR, and daily schedule. Executes the sanity test suite against the **Desktop Web** platform in headless mode.
- **On-Demand Workflow (`.github/workflows/on-demand.yml`):** Manually triggered via GitHub UI (`workflow_dispatch`) with customizable parameters (environment, marker filter) targeting the **Desktop Web** platform.

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
3. **Real Device Execution:** `--platform android-device` uses **Appium 2 + UiAutomator2** to launch Chrome on a real device or emulator, then attaches Playwright over CDP so the same Page Objects run unchanged.
4. **CI Scope:** Continuous Integration pipelines (GitHub Actions) run on headless Linux runners targeting the **Desktop Web** platform for high-speed, deterministic verification.
