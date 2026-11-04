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

Test Result: 4 tests passed.

## 6. Installation and Execution

Install dependencies:

```
pip install -r requirements.txt
```

Set the SECRET_KEY environment variable before running the application.

Run the application:

```
python app.py
```

Open in your browser:

```
http://127.0.0.1:5000
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

* Stronger file-content validation
* Expanded automated security testing
* Improved deployment configuration
* Enhanced audit logging
