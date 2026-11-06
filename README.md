# TrustVault – Secure Document Sharing Platform

## 1. Project Overview

TrustVault is a secure document-sharing web application built using Python and Flask. It allows users to upload, share, access and manage documents with permission-based controls.

## 2. Technologies Used

* Python
* Flask
* Flask-Login
* Flask-SQLAlchemy
* SQLite
* Flask-WTF
* HTML
* CSS
* Pytest

## 3. Key Features

* User registration and login
* Admin and user roles
* Secure document upload
* Document sharing with Read and Edit permissions
* Permission revocation
* Document replacement
* Access control
* Audit logging
* File type and size validation
* CSRF protection

## 4. Security Measures

* Password hashing
* Authentication using Flask-Login
* Role-based access control
* CSRF protection using Flask-WTF
* Session cookie security settings
* File extension and signature validation
* Restricted document access

## 5. Automated Security Testing

Security tests are implemented using Pytest.

Test cases:

1. CSRF protection rejects POST requests without valid tokens.
2. Dashboard access is restricted to authenticated users.
3. Logout requires valid CSRF protection.
4. Document downloads require authentication.
5. Private documents cannot be accessed by unauthorized users.
6. Revoked users cannot download documents.
7. Normal users cannot access admin activity logs.
8. Read-only users cannot edit documents.
9. Users with Edit permission can replace documents.
10. Read-only users cannot replace documents.
11. Invalid file uploads are rejected.
12. Files exceeding the upload size limit are rejected.
13. Document owners can share documents.
14. Non-owners cannot share documents.
15. Document owners can revoke access.
16. Non-owners cannot revoke access.
17. Admin users can access documents.
18. Invalid sharing permissions are rejected.

Test Result: 18 tests passed.
## 6. Installation and Execution

### Prerequisites

* Python 3.13
* Git

### Step 1: Clone the repository

```bash
git clone https://github.com/ssreddy123/TrustVault.git
cd TrustVault
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure environment variables

On Windows PowerShell:

```powershell
$env:SECRET_KEY = "your-secret-key"
$env:ADMIN_PASSWORD = "your-admin-password"
```

Use your own secret values. Do not commit them to GitHub.

`ADMIN_PASSWORD` is required when the application creates the initial admin account. If an admin account already exists in the database, it is not recreated.

### Step 5: Run the application

```bash
python app.py
```

The database tables are created automatically.

### Step 6: Open the application

Visit:

```text
http://127.0.0.1:5000
```

Register a normal user account through the registration page.

### Step 7: Run automated tests

```bash
pytest -v
```

Latest test result: 18 passed.

```

## 7. Project Structure

```
TrustVault/
├── app.py
├── requirements.txt
├── test_security.py
├── README.md
├── PROMPTS.md
├── THREATS.md
├── templates/
└── static/
```

## 8. Future Improvements

* Implement document search and filtering.
* Add support for additional document formats.
* Improve audit log filtering and reporting.
* Implement cloud-based document storage.
* Enhance mobile responsiveness.
* Add automated deployment and monitoring.
