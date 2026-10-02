from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoginLocators:
    # Portal header triggers
    NAV_PROFILE_TRIGGER: str = "button:has(img[alt='avatar'])"
    NAV_LOGIN_BUTTON: str = "button:has-text('Login'), a:has-text('Login')"
    MOBILE_MENU_TRIGGER: str = "button.xl\\:hidden:has(img[alt='avatar'])"

    # Login Modal / Auth Form elements
    MODAL_CONTAINER: str = "[role='dialog'], .modal, div[class*='Modal'], div[class*='login']"
    USERNAME_INPUT: str = "#username, input[type='email'], input[name='email'], input[placeholder*='email' i]"
    PASSWORD_INPUT: str = "#password, input[type='password'], input[name='password']"
    SUBMIT_BUTTON: str = "button[type='submit'], #kc-login, button:has-text('Login'), button:has-text('Continue')"
    CLOSE_BUTTON: str = "button[aria-label='Close'], button:has-text('✕'), button:has-text('×')"

    # Social Login (Facebook)
    FACEBOOK_LOGIN_BUTTON: str = (
        "button:has-text('Facebook'), button:has(img[alt*='facebook' i]), "
        "[data-testid*='facebook' i], button:has-text('Continue with Facebook')"
    )
    FB_EMAIL_INPUT: str = "#email, input[name='email'], input[type='email']"
    FB_PASSWORD_INPUT: str = "#pass, input[name='pass'], input[type='password']"
    FB_LOGIN_BUTTON: str = "#loginbutton, button[name='login'], button[type='submit']"
    FB_CONTINUE_BUTTON: str = "button:has-text('Continue as'), button[name='__CONFIRM__']"

    # Error alerts
    ERROR_CONTAINER: str = (
        "#input-error, .alert-error, .pf-c-alert.pf-m-danger, "
        "[role='alert'], .text-red-500, [data-testid='error-message']"
    )
