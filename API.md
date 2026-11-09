# TrustVault - Route and Access Documentation

## 1. Overview

TrustVault uses Flask routes to handle authentication, email verification, password recovery, document management, sharing, permission management, and administrative activities.

## 2. Application Routes

| Route | Method | Access |
|---|---|---|
| `/` | GET | Public |
| `/register` | GET, POST | Public |
| `/login` | GET, POST | Public |
| `/logout` | POST | Authenticated users |
| `/dashboard` | GET | Authenticated users |
| `/verify-email/<token>` | GET | Public with valid verification token |
| `/resend-verification` | GET, POST | Public |
| `/forgot-password` | GET, POST | Public |
| `/reset-password/<token>` | GET, POST | Public with valid reset token |
| `/account/email` | GET, POST | Authenticated users |
| `/upload` | POST | Authenticated users |
| `/replace/<doc_id>` | POST | Document owner or user with Edit permission |
| `/share/<doc_id>` | POST | Document owner |
| `/delete/<doc_id>` | POST | Document owner |
| `/revoke/<doc_id>/<user_id>` | POST | Document owner |
| `/download/<doc_id>` | GET | Document owner, authorized users or admin |
| `/logs` | GET | Admin only |

## 3. Authentication

- Registration creates a user account using a username, email address, and password.
- Email verification is required for newly registered accounts.
- Login verifies the user's credentials.
- Users with an unverified email address cannot log in.
- Existing accounts without an email address can continue to log in.
- Passwords are stored using password hashing.
- Flask-Login manages authenticated sessions.
- Protected routes require users to log in.

## 4. Email Verification

- Registration sends an email verification link.
- The verification link contains a unique account token.
- Verification tokens are stored as hashes in the database.
- Verification tokens expire after their configured validity period.
- Users can request another verification email.
- Successfully verified accounts can log in.

## 5. Password Recovery

- Users can request a password reset through the forgot-password page.
- A password reset link is sent to the registered email address.
- Password reset tokens are stored as hashes.
- Reset tokens expire after 15 minutes.
- Reset tokens can only be used once.
- New passwords are validated before updating the account.
- Invalid, expired, or previously used tokens are rejected.

## 6. Document Permissions

TrustVault supports two sharing permissions:

**Read**

- Allows an authorized user to access and download a shared document.
- Does not allow document replacement.

**Edit**

- Allows an authorized user to access and replace a shared document.

Document owners can share documents and revoke permissions. Administrators can access documents through the admin role.

## 7. Security Controls

- CSRF protection is enabled for form submissions.
- Unauthorized document access is restricted through server-side permission checks.
- Document ownership and sharing permissions protect document operations.
- Read and Edit permissions are enforced separately.
- Administrative activity logs are restricted to administrators.
- Unauthorized download, share, and revoke attempts are recorded in the audit log.
- Passwords are stored using secure password hashing.
- Account verification and password reset tokens are hashed before storage.
- Account tokens have expiration and single-use validation.
- SMTP credentials are configured through environment variables.

## 8. Important Notes

- All POST routes require valid CSRF protection.
- Document IDs and user IDs are passed through route parameters where required.
- Access is checked by the application before protected document operations are performed.
- Email functionality requires valid SMTP configuration.
- Audit logs are stored in the application's SQLite database and are not tamper-proof.
- The application is a working prototype and requires further security improvements before production deployment.