# TrustVault – Security Threat Model

## 1. Project Overview

TrustVault is a Flask-based document-sharing application. It allows users to upload documents, share them with specific users, manage permissions and track document activities.

## 2. Important Assets

* User accounts and passwords
* Uploaded documents
* Document permissions
* Activity logs
* Application configuration and secret key

## 3. Potential Security Threats

| Threat                       | Possible Impact               | Protection                          |
| ---------------------------- | ----------------------------- | ----------------------------------- |
| Unauthorized login           | Account compromise            | Password hashing and authentication |
| Unauthorized document access | Private data exposure         | Ownership and permission checks     |
| Malicious file uploads       | Unsafe files stored           | File validation and size limits     |
| Permission abuse             | Unauthorized document sharing | Ownership validation                |
| CSRF attacks                 | Unauthorized actions          | Flask-WTF CSRF protection           |
| Path traversal               | Unauthorized file access      | Controlled file handling            |
| Information leakage          | Exposure of sensitive data    | Secure configuration                |
| Audit log misuse             | Loss of accountability        | Restricted log access               |

## 4. Existing Security Measures

TrustVault currently implements:

* Password hashing using Werkzeug.
* User authentication using Flask-Login.
* Document ownership and permission checks.
* Read and Edit sharing permissions.
* Permission revocation.
* File extension validation.
* Basic file signature validation.
* Maximum upload size of 5 MB.
* CSRF protection using Flask-WTF.
* Environment-based secret key configuration.
* HTTP-only and SameSite session cookie settings.
* Restricted administrative activity logs.

## 5. Accepted Risks and Future Improvements

TrustVault is a challenge project and is not yet intended for production use.

Some known limitations are:

* Login attempts are not rate-limited.
* File validation may not detect every malicious file.
* Audit logs are stored in the application database and are not tamper-proof.
* SQLite is used instead of a production-scale database.
* Additional security testing and deployment hardening are needed.

These limitations are accepted for the current project version and should be addressed before production deployment.

## 6. Security Testing

Automated security tests are implemented using Pytest.

The test suite contains 20 tests covering:

* CSRF protection.
* Login requirements.
* Private document access.
* Revoked permission restrictions.
* Read and Edit permission enforcement.
* Document replacement permissions.
* File upload validation and size limits.
* Document sharing and access revocation.
* Ownership restrictions.
* Administrative log access.
* Invalid sharing permissions.

**Latest test result: 20 passed, 19 warnings.**

Manual testing also covered registration, login, document uploads, downloads, sharing and permission revocation.

## 7. Current Security Status

TrustVault includes authentication, authorization, document access controls, file validation and CSRF protection.

All 20 automated tests currently pass.

However, the application still has known limitations. Further security improvements and testing are required before it can be considered suitable for production use.
