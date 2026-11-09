# TrustVault - Security Threat Model



## 1. Project Overview



TrustVault is a Flask-based document-sharing application. It allows users to upload documents, share them with specific users, manage permissions, and track document activities.



The application also provides email verification and password recovery features to improve account security.



## 2. Important Assets



- User accounts and passwords

- Registered email addresses

- Uploaded documents

- Document permissions

- Account verification and password reset tokens

- Activity logs

- Application configuration and secret keys

- SMTP credentials



## 3. Potential Security Threats



| Threat | Possible Impact | Protection |

|---|---|---|

| Unauthorized login | Account compromise | Password hashing and authentication |

| Unauthorized document access | Private data exposure | Ownership and permission checks |

| Malicious file uploads | Unsafe files stored | File validation and size limits |

| Permission abuse | Unauthorized document sharing | Ownership validation |

| CSRF attacks | Unauthorized actions | Flask-WTF CSRF protection |

| Path traversal | Unauthorized file access | Controlled file handling |

| Information leakage | Exposure of sensitive data | Secure configuration |

| Audit log misuse | Loss of accountability | Restricted log access |

| Email account compromise | Unauthorized account recovery | Email verification and token expiration |

| Password reset token theft | Unauthorized password changes | Hashed, expiring, single-use tokens |

| SMTP credential exposure | Unauthorized email access | Environment-based credential storage |

| Token reuse | Repeated account verification or password reset | Single-use token validation |



## 4. Existing Security Measures



TrustVault currently implements:



- Password hashing using Werkzeug.

- User authentication using Flask-Login.

- Email verification for newly registered accounts.

- Password recovery through email links.

- Hashed storage of account verification and password reset tokens.

- Token expiration and single-use validation.

- Password validation during password reset.

- Document ownership and permission checks.

- Read and Edit sharing permissions.

- Permission revocation.

- File extension validation.

- Basic file signature validation.

- Maximum upload size of 5 MB.

- CSRF protection using Flask-WTF.

- Environment-based secret key configuration.

- SMTP credentials configured through environment variables.

- HTTP-only and SameSite session cookie settings.

- Restricted administrative activity logs.

- Audit logging of unauthorized download, share, and revoke attempts.



## 5. Accepted Risks and Future Improvements



TrustVault is a challenge project and is not yet intended for production use.



Some known limitations are:



- Login attempts are not rate-limited.

- Password reset requests are not rate-limited.

- File validation may not detect every malicious file.

- Email security depends partly on the security of the user's email account.

- Email delivery depends on the configured SMTP service.

- Audit logs are stored in the application database and are not tamper-proof.

- SQLite is used instead of a production-scale database.

- Additional security testing and deployment hardening are needed.



These limitations should be addressed before production deployment.



## 6. Security Testing



Automated security tests are implemented using Pytest.



The test suite contains 29 tests covering:



- CSRF protection.

- Login requirements.

- Private document access.

- Revoked permission restrictions.

- Read and Edit permission enforcement.

- Document replacement permissions.

- File upload validation and size limits.

- Document sharing and access revocation.

- Ownership restrictions.

- Administrative log access.

- Invalid sharing permissions.

- Unauthorized download attempts are logged.

- Unauthorized share attempts are logged.

- Unauthorized revoke attempts are logged.

- Successful email verification.

- Expired verification token rejection.

- Successful password reset.

- Short password rejection.

- Password mismatch rejection.

- Password reset token reuse prevention.



**Latest test result: 29 passed, 33 warnings (2026-11-09).**



Manual testing also covered registration, email verification, login, password recovery, document uploads, downloads, sharing, and permission revocation.



## 7. Current Security Status



TrustVault includes authentication, authorization, document access controls, file validation, CSRF protection, email verification, password recovery, and audit logging.



All 29 automated tests currently pass.



However, the application still has known limitations. Further security improvements and testing are required before it can be considered suitable for production use.
