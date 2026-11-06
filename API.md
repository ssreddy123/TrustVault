# TrustVault – Route and Access Documentation

## 1. Overview

TrustVault uses Flask routes to handle authentication, document management, sharing and administrative activities.

## 2. Application Routes

| Route                        | Method    | Access                                      |
| ---------------------------- | --------- | ------------------------------------------- |
| `/`                          | GET       | Public                                      |
| `/register`                  | GET, POST | Public                                      |
| `/login`                     | GET, POST | Public                                      |
| `/logout`                    | POST      | Authenticated users                         |
| `/dashboard`                 | GET       | Authenticated users                         |
| `/upload`                    | POST      | Authenticated users                         |
| `/replace/<doc_id>`          | POST      | Document owner or user with Edit permission |
| `/share/<doc_id>`            | POST      | Document owner                              |
| `/revoke/<doc_id>/<user_id>` | POST      | Document owner                              |
| `/download/<doc_id>`         | GET       | Document owner, authorized users or admin   |
| `/logs`                      | GET       | Admin only                                  |

## 3. Authentication

* Registration creates a user account.
* Login verifies the user's credentials.
* Passwords are stored using password hashing.
* Flask-Login manages authenticated sessions.
* Protected routes require users to log in.

## 4. Document Permissions

TrustVault supports two sharing permissions:

**Read**

* Allows an authorized user to access and download a shared document.
* Does not allow document replacement.

**Edit**

* Allows an authorized user to access and replace a shared document.

Document owners can share documents and revoke permissions.

## 5. Security Controls

* CSRF protection is enabled for form submissions.
* Unauthorized document access is restricted.
* Ownership and permission checks protect document operations.
* Administrative activity logs are restricted to administrators.

## 6. Important Notes

* All POST routes require valid CSRF protection.
* Document IDs and user IDs are passed through route parameters where required.
* Access is checked by the application before protected document operations are performed.
