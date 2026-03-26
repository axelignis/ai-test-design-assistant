# Example Output

Generated from `examples/login_feature.txt` using `LLM_PROVIDER=ollama` with `qwen2.5:7b`.

---

# Test Design Report

## Executive Summary

- **Source type:** User Story
- **Positive scenarios:** 5
- **Negative scenarios:** 5
- **Edge cases:** 5
- **Clarification questions:** 5
- **Risks:** 5

## Positive Scenarios

- User logs in successfully using correct email and password
- User accesses personal dashboard after successful login
- User receives password reset link via email when clicking 'forgot password'
- Session expires automatically after 30 minutes of inactivity
- User is redirected to the last viewed page upon successful login

## Negative Scenarios

- Invalid email format prevents form submission
- Incorrect password with valid email shows generic error message
- More than 5 consecutive failed attempts locks account for 15 minutes
- System rejects empty fields in login form
- User sees no change after clicking 'forgot password' link

## Edge Cases

- User enters a very long email address that exceeds the input field limit
- Password is extremely weak and may trigger a security alert
- User logs in using an uppercase version of their email address
- Login attempt made via mobile device with limited keyboard options
- Session expires while user has multiple tabs open, requiring re-login

## Clarification Questions

- What is the maximum length for the email input field?
- How should the system handle typos in the 'forgot password' link?
- Is there a limit to how many password reset links can be sent per day?
- Should sessions be invalidated when user changes their device or browser?
- Can users access their account if they are locked out due to failed attempts?

## Risks

- Security vulnerabilities in handling and storing passwords
- Potential for denial of service by brute-forcing login attempts
- Incorrect session expiration may lead to unauthorized access
- Logging mechanism might expose sensitive information about user activity
- Inconsistent behavior across different devices or browsers

## Requirement Snapshot

> As a registered user, I want to log in to my account using my email address and
> password so that I can access my personal dashboard and settings.
>
> Acceptance Criteria:
> - The login form accepts an email address and password
> - Valid credentials redirect the user to their dashboard
> - Invalid credentials display an error message without revealing which field is wrong
> - Passwords are never displayed in plain text
> - After 5 consecutive failed attempts, the account is temporarily locked for 15 minutes
> - A "forgot password" link allows users to initiate a password reset via email
> - Sessions expire after 30 minutes of inactivity
> - Login activity is recorded in the user's account audit log
