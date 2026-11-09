# TrustVault – Secure Document Sharing Platform

## 1. Project Overview

TrustVault is a secure document-sharing web application built using Python and Flask. It allows users to upload, share, access, and manage documents with permission-based controls.

The application provides Read and Edit permissions, allowing document owners to control who can access their files. Administrators have administrative access, document owners control their own documents, and viewers receive access through sharing permissions.

## Live Demo

https://siva04.pythonanywhere.com/

## 2. Technologies Used

* Python 3.13
* Flask
* Flask-Login
* Flask-SQLAlchemy
* SQLite
* Flask-WTF
* HTML
* CSS
* Pytest
* Git and GitHub

## 3. Key Features

* User registration and login
* Admin and user roles
* Secure document upload
* Document sharing with Read and Edit permissions
* Permission revocation
* Document replacement
* Authentication and access control
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
* Permission-based document operations

## 5. Automated Security Testing

Security tests are implemented using Pytest.

### Test Cases

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
19. Document owners can delete their documents.
20. Non-owners cannot delete documents.
21. Unauthorized download attempts are recorded in the audit log.
22. Unauthorized share attempts are recorded in the audit log.
23. Unauthorized revoke attempts are recorded in the audit log.

**Latest Test Result: 23 tests passed, 29 warnings (2026-11-09).**

## 6. Installation and Execution

### Prerequisites

* Python 3.13
* Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/ssreddy123/TrustVault.git
cd TrustVault
```

### Step 2: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

On Windows PowerShell:

```powershell
$env:SECRET_KEY = "your-secret-key"
$env:ADMIN_PASSWORD = "your-admin-password"
```

Use your own secret values. Do not commit them to GitHub.

`ADMIN_PASSWORD` is required when the application creates the initial admin account. If an admin account already exists in the database, it is not recreated.

### Step 5: Run the Application

```bash
python app.py
```

The database tables are created automatically when the application initializes.

### Step 6: Open the Application

Visit:

```text
http://127.0.0.1:5000
```

Register a normal user account through the registration page.

### Step 7: Run Automated Tests

```bash
pytest -v
```

Latest test result: **23 passed, 29 warnings (2026-11-09).**

## 7. Demo Setup

For a fresh database, follow these steps to demonstrate the application's functionality:

1. Start the application with `SECRET_KEY` and `ADMIN_PASSWORD` configured.
2. Log in using the username `admin` and the admin password configured through the environment variable.
3. Register two normal user accounts.
4. Log in as the first user and upload a sample document.
5. Share the document with the second user using Read or Edit permission.
6. Log in as the second user and test the granted access.
7. Test document replacement and permission revocation.

**Note:** No default user passwords or preloaded sample documents are included. Users must register their own accounts.

## 8. Project Structure

```text
TrustVault/
│
├── app.py
├── requirements.txt
├── test_security.py
├── README.md
├── API.md
├── PROMPTS.md
├── THREATS.md
│
├── templates/
│   ├── dashboard.html
│   ├── login.html
│   └── register.html
│
└── static/
    └── style.css
```

## 9. Documentation

Additional project documentation:

* **API.md** – Application routes and access permissions.
* **THREATS.md** – Security threats, existing protections, and limitations.
* **PROMPTS.md** – AI tools used, prompts, outputs, and verification process.

## 10. Future Improvements

* Implement document search and filtering.
* Add support for additional document formats.
* Improve audit log filtering and reporting.
* Implement cloud-based document storage.
* Enhance mobile responsiveness.
* Add automated deployment and monitoring.

## 11. Project Status

TrustVault currently includes user authentication, document sharing, permission management, access control, audit logging, and automated security tests.

The project is a working prototype. Additional improvements are needed before production deployment.
