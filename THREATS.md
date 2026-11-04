# TrustVault – Security Threat Model

## 1. Project Overview

TrustVault is a secure document-sharing web application built using Python and Flask. It allows users to upload documents, share them with other users, manage permissions and monitor document activities.

## 2. Important Assets

* User account information
* Uploaded documents
* User passwords
* Document-sharing permissions
* Activity logs
* Application configuration and secret key

## 3. Potential Security Threats

| Threat                       | Possible Impact                   | Security Protection                      |
| ---------------------------- | --------------------------------- | ---------------------------------------- |
| Unauthorized login           | Account compromise                | Password hashing and authentication      |
| Unauthorized document access | Private data exposure             | Ownership and permission checks          |
| Malicious file uploads       | Unsafe files stored               | Extension, signature and size validation |
| Password attacks             | Account compromise                | Password validation                      |
| Permission abuse             | Unauthorized sharing              | Role and ownership validation            |
| CSRF attacks                 | Unauthorized actions              | Flask-WTF CSRF protection                |
| Path traversal               | Unauthorized file access          | Controlled file handling                 |
| Information leakage          | Exposure of sensitive information | Secure configuration and error handling  |
| Audit log misuse             | Loss of accountability            | Restricted log access                    |

## 4. Existing Security Measures

The following protections are currently implemented:

* Password hashing using Werkzeug.
* User authentication using Flask-Login.
* Role-based access control.
* Document ownership and permission checks.
* File extension allowlisting.
* Basic file signature and structure validation.
* Maximum upload size restriction of 5 MB.
* CSRF protection using Flask-WTF.
* Environment-based secret key configuration.
* HTTP-only and SameSite session cookie settings.
* Restricted access to administrative activity logs.
* Debug mode disabled.

## 5. Security Improvements Required

The following improvements are recommended:

* Implement login attempt rate limiting.
* Strengthen file-content validation.
* Improve error handling and security monitoring.
* Add more automated access-control tests.
* Review database transaction and file-storage consistency.
* Configure secure session cookies for HTTPS deployment.
* Conduct additional security testing before production deployment.

## 6. Security Testing

Automated tests are implemented using Pytest.

Current automated test cases:

1. Reject POST requests without valid CSRF tokens.
2. Prevent unauthenticated dashboard access.
3. Reject logout requests without CSRF tokens.
4. Prevent unauthenticated document downloads.

Automated test result: 4 tests passed.

Additional manual tests performed:

* Private document access restrictions.
* Read and Edit permission verification.
* Document sharing and revocation.
* Document replacement permissions.
* Administrative activity log access.

## 7. Current Security Status

TrustVault includes multiple security protections covering authentication, authorization, document access, file validation and CSRF protection.

Four automated security tests currently pass.

However, the application is still under development. Additional security testing, deployment hardening and review are required before production use.
