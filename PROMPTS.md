# AI Usage Documentation – TrustVault

## AI Tool Used

ChatGPT (GPT-6)

## Development Log

### Entry 1 – Flask Application (2026-11-05)

* Prompt: How can I build a document-sharing application using Flask?
* AI output: Suggested a Flask application structure and database integration.
* My verification: Reviewed the generated structure and tested the application.
* Related commit: https://github.com/ssreddy123/TrustVault/commit/c2aed7c

### Entry 2 – Authentication and Access Control (2026-11-05)

* Prompt: How can I implement login, registration and restrict access to private documents?
* AI output: Suggested authentication and permission-checking approaches.
* My verification: Tested login requirements and unauthorized document access.
* Related commit: https://github.com/ssreddy123/TrustVault/commit/c2aed7c

### Entry 3 – Document Sharing and Audit Logging (2026-11-05)

* Prompt: How can document owners share files with Read/Edit permissions and revoke access?
* AI output: Suggested permission-based sharing and activity logging.
* My verification: Tested sharing, permission changes and access revocation.
* Related commit: https://github.com/ssreddy123/TrustVault/commit/c2aed7c

### Entry 4 – Login Debugging (2026-11-05)

* Prompt: Help debug repeated login flash messages.
* AI output: Suggested checking the login route and template.
* What needed correction: The repeated messages were caused by old messages remaining in the session, not duplicate flash calls.
* My correction: Inspected the Flask route and template, refreshed the page and verified the behaviour.
* Related commits:

  * https://github.com/ssreddy123/TrustVault/commit/131d6c8
  * https://github.com/ssreddy123/TrustVault/commit/e997655

### Entry 5 – Dashboard Improvements (2026-11-05)

* Prompt: Help improve dashboard flash messages and layout.
* AI output: Suggested template changes.
* My verification: Reviewed the HTML and adjusted the dashboard presentation to match the intended design.
* Related commit: https://github.com/ssreddy123/TrustVault/commit/e997655

## Developer Responsibility

I reviewed AI-generated suggestions, tested application behaviour and made corrections where necessary. AI was used as an assistant; I remained responsible for the final implementation.

### Entry 6 – Unauthorized Access Audit Logging (2026-11-09)

* Prompt: How can I record unauthorized download, share and revoke attempts in the audit log?
* AI output: Suggested recording denied access attempts and testing the audit behaviour.
* My verification: Added security tests for unauthorized download, share and revoke attempts. All 23 security tests passed.
* Related commit: https://github.com/ssreddy123/TrustVault/commit/febc73b

### Entry 7 - Email Verification and Password Recovery (2026-11-09)

* Prompt: How can I implement email verification, resend verification links and secure password recovery in my Flask application?
* AI output: Suggested email-based verification, hashed account tokens, token expiration, single-use validation and password reset functionality.
* My verification: Tested registration, email verification and password recovery manually. Added automated tests for successful verification, expired tokens, password reset, password validation and token reuse prevention. All 29 security tests passed.
* My correction: Reviewed the implementation, configured SMTP credentials through environment variables and tested the email workflow.
