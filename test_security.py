from app import (
    app, db, User, Document, Permission, AuditLog,
    AccountToken, can_access, create_account_token, utc_now
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user
from io import BytesIO
from datetime import timedelta
import uuid
import os


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def create_user(role='user'):
    unique_id = uuid.uuid4().hex[:8]

    with app.app_context():
        user = User(
            username=f'test_{unique_id}',
            password=generate_password_hash('test12345'),
            role=role
        )

        db.session.add(user)
        db.session.commit()

        return user.id


def create_email_user():
    user_id = create_user()

    with app.app_context():
        user = db.session.get(User, user_id)
        user.email = f'{uuid.uuid4().hex}@example.com'
        user.email_verified = False
        db.session.commit()

    return user_id


def create_document(owner_id):
    unique_id = uuid.uuid4().hex[:8]

    with app.app_context():
        document = Document(
            filename='test.txt',
            stored_name=f'test_{unique_id}.txt',
            owner_id=owner_id
        )

        db.session.add(document)
        db.session.commit()

        return document.id, document.stored_name


def login_client(client, user_id):
    with client.session_transaction(
        base_url='https://localhost'
    ) as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def cleanup(user_ids=None, document_ids=None, filenames=None):
    user_ids = user_ids or []
    document_ids = document_ids or []
    filenames = filenames or []

    with app.app_context():

        Permission.query.filter(
            Permission.document_id.in_(document_ids)
        ).delete(synchronize_session=False)

        AccountToken.query.filter(
            AccountToken.user_id.in_(user_ids)
        ).delete(synchronize_session=False)

        AuditLog.query.filter(
            AuditLog.user_id.in_(user_ids)
        ).delete(synchronize_session=False)

        for document_id in document_ids:
            document = db.session.get(Document, document_id)

            if document:
                db.session.delete(document)

        for user_id in user_ids:
            user = db.session.get(User, user_id)

            if user:
                db.session.delete(user)

        db.session.commit()

        for filename in filenames:
            if not filename:
                continue

            path = os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )

            if os.path.exists(path):
                os.remove(path)


# ==========================================
# TEST 1 - CSRF PROTECTION
# ==========================================

def test_csrf_protection():

    client = app.test_client()

    response = client.post('/login', data={
        'username': 'test',
        'password': 'wrong'
    })

    assert response.status_code == 400


# ==========================================
# TEST 2 - DASHBOARD LOGIN REQUIRED
# ==========================================

def test_dashboard_requires_login():

    client = app.test_client()

    response = client.get('/dashboard')

    assert response.status_code == 302


# ==========================================
# TEST 3 - LOGOUT CSRF PROTECTION
# ==========================================

def test_logout_requires_csrf():

    client = app.test_client()

    response = client.post('/logout')

    assert response.status_code == 400


# ==========================================
# TEST 4 - DOWNLOAD LOGIN REQUIRED
# ==========================================

def test_download_requires_login():

    client = app.test_client()

    response = client.get('/download/1')

    assert response.status_code == 302


# ==========================================
# TEST 5 - PRIVATE DOCUMENT ACCESS
# ==========================================

def test_private_document_access():

    owner_id = create_user()
    other_id = create_user()

    document_id, filename = create_document(owner_id)

    try:
        client = app.test_client()

        login_client(client, other_id)

        response = client.get(
            f'/download/{document_id}'
        )

        assert response.status_code == 403

    finally:
        cleanup(
            [owner_id, other_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 6 - REVOKED USER CANNOT DOWNLOAD
# ==========================================

def test_revoked_user_cannot_download():

    owner_id = create_user()
    reader_id = create_user()

    document_id, filename = create_document(owner_id)

    with app.app_context():
        permission = Permission(
            document_id=document_id,
            user_id=reader_id,
            access='read'
        )

        db.session.add(permission)
        db.session.commit()

        db.session.delete(permission)
        db.session.commit()

    try:
        client = app.test_client()

        login_client(client, reader_id)

        response = client.get(
            f'/download/{document_id}'
        )

        assert response.status_code == 403

    finally:
        cleanup(
            [owner_id, reader_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 7 - NORMAL USER CANNOT ACCESS LOGS
# ==========================================

def test_normal_user_cannot_access_logs():

    user_id = create_user()

    try:
        client = app.test_client()

        login_client(client, user_id)

        response = client.get('/logs')

        assert response.status_code == 403

    finally:
        cleanup([user_id])


# ==========================================
# TEST 8 - READ USER CANNOT EDIT
# ==========================================

def test_read_only_user_cannot_edit_document():

    owner_id = create_user()
    reader_id = create_user()

    document_id, filename = create_document(owner_id)

    with app.app_context():
        permission = Permission(
            document_id=document_id,
            user_id=reader_id,
            access='read'
        )

        db.session.add(permission)
        db.session.commit()

    try:
        with app.test_request_context():

            reader = db.session.get(User, reader_id)

            login_user(reader)

            document = db.session.get(Document, document_id)

            assert can_access(document, 'read') is True
            assert can_access(document, 'edit') is False

    finally:
        cleanup(
            [owner_id, reader_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 9 - EDIT USER CAN REPLACE DOCUMENT
# ==========================================

def test_edit_user_can_replace_document(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    owner_id = create_user()
    editor_id = create_user()

    document_id, filename = create_document(owner_id)

    with app.app_context():
        permission = Permission(
            document_id=document_id,
            user_id=editor_id,
            access='edit'
        )

        db.session.add(permission)
        db.session.commit()

        old_path = os.path.join(
            app.config['UPLOAD_FOLDER'], filename
        )

        with open(old_path, 'wb') as file:
            file.write(b'Old document')

    try:
        client = app.test_client()

        login_client(client, editor_id)

        response = client.post(
            f'/replace/{document_id}',
            data={
                'file': (
                    BytesIO(b'New document'),
                    'updated.txt'
                )
            },
            content_type='multipart/form-data'
        )

        assert response.status_code == 302

        with app.app_context():
            document = db.session.get(Document, document_id)

            assert document.filename == 'updated.txt'

    finally:
        with app.app_context():
            document = db.session.get(Document, document_id)

            new_filename = (
                document.stored_name if document else None
            )

        cleanup(
            [owner_id, editor_id],
            [document_id],
            [filename, new_filename] if new_filename else [filename]
        )


# ==========================================
# TEST 10 - READ USER CANNOT REPLACE DOCUMENT
# ==========================================

def test_read_user_cannot_replace_document(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    owner_id = create_user()
    reader_id = create_user()

    document_id, filename = create_document(owner_id)

    with app.app_context():
        permission = Permission(
            document_id=document_id,
            user_id=reader_id,
            access='read'
        )

        db.session.add(permission)
        db.session.commit()

    try:
        client = app.test_client()

        login_client(client, reader_id)

        response = client.post(
            f'/replace/{document_id}',
            data={
                'file': (
                    BytesIO(b'New document'),
                    'new.txt'
                )
            },
            content_type='multipart/form-data'
        )

        assert response.status_code == 403

    finally:
        cleanup(
            [owner_id, reader_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 11 - INVALID FILE UPLOAD
# ==========================================

def test_invalid_file_upload_rejected(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    user_id = create_user()

    try:
        client = app.test_client()

        login_client(client, user_id)

        response = client.post(
            '/upload',
            data={
                'file': (
                    BytesIO(b'Invalid executable content'),
                    'malware.exe'
                )
            },
            content_type='multipart/form-data'
        )

        assert response.status_code == 302

        with app.app_context():
            documents = Document.query.filter_by(
                owner_id=user_id
            ).all()

            assert len(documents) == 0

    finally:
        cleanup([user_id])


# ==========================================
# TEST 12 - FILE SIZE LIMIT
# ==========================================

def test_file_size_limit():

    client = app.test_client()

    response = client.post(
        '/upload',
        data={
            'file': (
                BytesIO(b'A' * (6 * 1024 * 1024)),
                'large.txt'
            )
        },
        content_type='multipart/form-data'
    )

    assert response.status_code == 413


# ==========================================
# TEST 13 - OWNER CAN SHARE DOCUMENT
# ==========================================

def test_owner_can_share_document(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    owner_id = create_user()
    recipient_id = create_user()

    document_id, filename = create_document(owner_id)

    try:
        with app.app_context():
            recipient = db.session.get(User, recipient_id)
            recipient_username = recipient.username

        client = app.test_client()

        login_client(client, owner_id)

        response = client.post(
            f'/share/{document_id}',
            data={
                'username': recipient_username,
                'access': 'read'
            }
        )

        assert response.status_code == 302

        with app.app_context():
            permission = Permission.query.filter_by(
                document_id=document_id,
                user_id=recipient_id
            ).first()

            assert permission is not None
            assert permission.access == 'read'

    finally:
        cleanup(
            [owner_id, recipient_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 14 - NON OWNER CANNOT SHARE
# ==========================================

def test_non_owner_cannot_share_document(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    owner_id = create_user()
    other_id = create_user()
    recipient_id = create_user()

    document_id, filename = create_document(owner_id)

    try:
        with app.app_context():
            recipient = db.session.get(User, recipient_id)
            recipient_username = recipient.username

        client = app.test_client()

        login_client(client, other_id)

        response = client.post(
            f'/share/{document_id}',
            data={
                'username': recipient_username,
                'access': 'read'
            }
        )

        assert response.status_code == 302

        with app.app_context():
            permission = Permission.query.filter_by(
                document_id=document_id,
                user_id=recipient_id
            ).first()

            assert permission is None

    finally:
        cleanup(
            [owner_id, other_id, recipient_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 15 - OWNER CAN REVOKE ACCESS
# ==========================================

def test_owner_can_revoke_access(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    owner_id = create_user()
    reader_id = create_user()

    document_id, filename = create_document(owner_id)

    with app.app_context():
        permission = Permission(
            document_id=document_id,
            user_id=reader_id,
            access='read'
        )

        db.session.add(permission)
        db.session.commit()

    try:
        client = app.test_client()

        login_client(client, owner_id)

        response = client.post(
            f'/revoke/{document_id}/{reader_id}'
        )

        assert response.status_code == 302

        with app.app_context():
            permission = Permission.query.filter_by(
                document_id=document_id,
                user_id=reader_id
            ).first()

            assert permission is None

    finally:
        cleanup(
            [owner_id, reader_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 16 - NON OWNER CANNOT REVOKE ACCESS
# ==========================================

def test_non_owner_cannot_revoke_access(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    owner_id = create_user()
    other_id = create_user()
    reader_id = create_user()

    document_id, filename = create_document(owner_id)

    with app.app_context():
        permission = Permission(
            document_id=document_id,
            user_id=reader_id,
            access='read'
        )

        db.session.add(permission)
        db.session.commit()

    try:
        client = app.test_client()

        login_client(client, other_id)

        response = client.post(
            f'/revoke/{document_id}/{reader_id}'
        )

        assert response.status_code == 302

        with app.app_context():
            permission = Permission.query.filter_by(
                document_id=document_id,
                user_id=reader_id
            ).first()

            assert permission is not None

    finally:
        cleanup(
            [owner_id, other_id, reader_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 17 - ADMIN CAN ACCESS DOCUMENT
# ==========================================

def test_admin_can_access_document():

    owner_id = create_user()
    admin_id = create_user(role='admin')

    document_id, filename = create_document(owner_id)

    file_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )

    with open(file_path, 'wb') as file:
        file.write(b'Admin test document')

    response = None

    try:
        client = app.test_client()

        login_client(client, admin_id)

        response = client.get(
            f'/download/{document_id}'
        )

        assert response.status_code == 200

    finally:
        if response is not None:
            response.close()

        cleanup(
            [owner_id, admin_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 18 - INVALID SHARE PERMISSION
# ==========================================

def test_invalid_share_permission_rejected(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    owner_id = create_user()
    recipient_id = create_user()

    document_id, filename = create_document(owner_id)

    try:
        with app.app_context():
            recipient = db.session.get(User, recipient_id)
            recipient_username = recipient.username

        client = app.test_client()

        login_client(client, owner_id)

        response = client.post(
            f'/share/{document_id}',
            data={
                'username': recipient_username,
                'access': 'admin'
            }
        )

        assert response.status_code == 302

        with app.app_context():
            permission = Permission.query.filter_by(
                document_id=document_id,
                user_id=recipient_id
            ).first()

            assert permission is None

    finally:
        cleanup(
            [owner_id, recipient_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 19 - OWNER CAN DELETE DOCUMENT
# ==========================================

def test_owner_can_delete_document(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    owner_id = create_user()
    recipient_id = create_user()

    document_id, filename = create_document(owner_id)

    try:
        file_path = os.path.join(
            app.config['UPLOAD_FOLDER'], filename
        )

        with open(file_path, 'wb') as f:
            f.write(b'Test document')

        with app.app_context():
            permission = Permission(
                document_id=document_id,
                user_id=recipient_id,
                access='read'
            )
            db.session.add(permission)
            db.session.commit()

        client = app.test_client()
        login_client(client, owner_id)

        response = client.post(
            f'/delete/{document_id}'
        )

        assert response.status_code == 302

        with app.app_context():
            assert db.session.get(
                Document, document_id
            ) is None

            assert Permission.query.filter_by(
                document_id=document_id
            ).first() is None

            assert AuditLog.query.filter_by(
                user_id=owner_id,
                action='DELETE'
            ).first() is not None

        assert not os.path.exists(file_path)

    finally:
        cleanup(
            [owner_id, recipient_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 20 - NON-OWNER CANNOT DELETE DOCUMENT
# ==========================================

def test_non_owner_cannot_delete_document(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    owner_id = create_user()
    other_user_id = create_user()

    document_id, filename = create_document(owner_id)

    try:
        client = app.test_client()
        login_client(client, other_user_id)

        response = client.post(
            f'/delete/{document_id}'
        )

        assert response.status_code == 302

        with app.app_context():
            assert db.session.get(
                Document, document_id
            ) is not None

    finally:
        cleanup(
            [owner_id, other_user_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 21 - UNAUTHORIZED DOWNLOAD IS LOGGED
# ==========================================

def test_unauthorized_download_is_logged():

    owner_id = create_user()
    other_user_id = create_user()

    document_id, filename = create_document(owner_id)

    try:
        client = app.test_client()

        login_client(client, other_user_id)

        response = client.get(
            f'/download/{document_id}'
        )

        assert response.status_code == 403

        with app.app_context():

            log = AuditLog.query.filter_by(
                user_id=other_user_id,
                action='ACCESS_DENIED'
            ).first()

            assert log is not None
            assert str(document_id) in log.details

    finally:
        cleanup(
            [owner_id, other_user_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 22 - UNAUTHORIZED SHARE IS LOGGED
# ==========================================

def test_unauthorized_share_is_logged(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    owner_id = create_user()
    other_id = create_user()
    recipient_id = create_user()

    document_id, filename = create_document(owner_id)

    try:
        with app.app_context():
            recipient = db.session.get(User, recipient_id)
            username = recipient.username

        client = app.test_client()
        login_client(client, other_id)

        response = client.post(
            f'/share/{document_id}',
            data={
                'username': username,
                'access': 'read'
            }
        )

        assert response.status_code == 302

        with app.app_context():
            log = AuditLog.query.filter_by(
                user_id=other_id,
                action='ACCESS_DENIED'
            ).first()

            assert log is not None
            assert str(document_id) in log.details

    finally:
        cleanup(
            [owner_id, other_id, recipient_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 23 - UNAUTHORIZED REVOKE IS LOGGED
# ==========================================

def test_unauthorized_revoke_is_logged(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    owner_id = create_user()
    other_id = create_user()
    reader_id = create_user()

    document_id, filename = create_document(owner_id)

    try:
        with app.app_context():
            permission = Permission(
                document_id=document_id,
                user_id=reader_id,
                access='read'
            )

            db.session.add(permission)
            db.session.commit()

        client = app.test_client()
        login_client(client, other_id)

        response = client.post(
            f'/revoke/{document_id}/{reader_id}'
        )

        assert response.status_code == 302

        with app.app_context():
            log = AuditLog.query.filter_by(
                user_id=other_id,
                action='ACCESS_DENIED'
            ).first()

            assert log is not None

            permission = Permission.query.filter_by(
                document_id=document_id,
                user_id=reader_id
            ).first()

            assert permission is not None

    finally:
        cleanup(
            [owner_id, other_id, reader_id],
            [document_id],
            [filename]
        )


# ==========================================
# TEST 24 - EMAIL VERIFICATION SUCCESS
# ==========================================

def test_email_verification_success():

    user_id = create_email_user()

    try:
        with app.app_context():
            user = db.session.get(User, user_id)

            token = create_account_token(
                user, 'verify_email'
            )

        client = app.test_client()

        response = client.get(
            f'/verify-email/{token}',
            follow_redirects=True
        )

        assert response.status_code == 200

        with app.app_context():
            user = db.session.get(User, user_id)

            assert user.email_verified is True

            account_token = AccountToken.query.filter_by(
                user_id=user_id,
                purpose='verify_email'
            ).first()

            assert account_token.used_at is not None

    finally:
        cleanup([user_id])


# ==========================================
# TEST 25 - EXPIRED VERIFICATION TOKEN REJECTED
# ==========================================

def test_expired_verification_token_rejected():

    user_id = create_email_user()

    try:
        with app.app_context():
            user = db.session.get(User, user_id)

            token = create_account_token(
                user, 'verify_email'
            )

            account_token = AccountToken.query.filter_by(
                user_id=user_id,
                purpose='verify_email'
            ).first()

            account_token.expires_at = (
                utc_now() - timedelta(minutes=1)
            )

            db.session.commit()

        client = app.test_client()

        response = client.get(
            f'/verify-email/{token}',
            follow_redirects=True
        )

        assert response.status_code == 200

        with app.app_context():
            user = db.session.get(User, user_id)

            assert user.email_verified is False

    finally:
        cleanup([user_id])


# ==========================================
# TEST 26 - PASSWORD RESET SUCCESS
# ==========================================

def test_password_reset_success(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    user_id = create_email_user()

    try:
        with app.app_context():
            user = db.session.get(User, user_id)
            user.email_verified = True
            db.session.commit()

            token = create_account_token(
                user, 'password_reset'
            )

        client = app.test_client()

        response = client.post(
            f'/reset-password/{token}',
            data={
                'password': 'NewPassword123',
                'confirm_password': 'NewPassword123'
            },
            follow_redirects=True
        )

        assert response.status_code == 200

        with app.app_context():
            user = db.session.get(User, user_id)

            assert check_password_hash(
                user.password,
                'NewPassword123'
            )

            account_token = AccountToken.query.filter_by(
                user_id=user_id,
                purpose='password_reset'
            ).first()

            assert account_token.used_at is not None

    finally:
        cleanup([user_id])


# ==========================================
# TEST 27 - PASSWORD RESET REJECTS SHORT PASSWORD
# ==========================================

def test_password_reset_rejects_short_password(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    user_id = create_email_user()

    try:
        with app.app_context():
            user = db.session.get(User, user_id)

            token = create_account_token(
                user, 'password_reset'
            )

        client = app.test_client()

        response = client.post(
            f'/reset-password/{token}',
            data={
                'password': 'short',
                'confirm_password': 'short'
            },
            follow_redirects=True
        )

        assert response.status_code == 200

        with app.app_context():
            account_token = AccountToken.query.filter_by(
                user_id=user_id,
                purpose='password_reset'
            ).first()

            assert account_token.used_at is None

    finally:
        cleanup([user_id])


# ==========================================
# TEST 28 - PASSWORD RESET REJECTS MISMATCH
# ==========================================

def test_password_reset_rejects_mismatched_passwords(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    user_id = create_email_user()

    try:
        with app.app_context():
            user = db.session.get(User, user_id)

            token = create_account_token(
                user, 'password_reset'
            )

        client = app.test_client()

        response = client.post(
            f'/reset-password/{token}',
            data={
                'password': 'Password123',
                'confirm_password': 'Different123'
            },
            follow_redirects=True
        )

        assert response.status_code == 200

        with app.app_context():
            account_token = AccountToken.query.filter_by(
                user_id=user_id,
                purpose='password_reset'
            ).first()

            assert account_token.used_at is None

    finally:
        cleanup([user_id])


# ==========================================
# TEST 29 - PASSWORD RESET TOKEN CANNOT BE REUSED
# ==========================================

def test_password_reset_token_cannot_be_reused(monkeypatch):

    monkeypatch.setitem(
        app.config, 'WTF_CSRF_ENABLED', False
    )

    user_id = create_email_user()

    try:
        with app.app_context():
            user = db.session.get(User, user_id)

            token = create_account_token(
                user, 'password_reset'
            )

        client = app.test_client()

        client.post(
            f'/reset-password/{token}',
            data={
                'password': 'NewPassword123',
                'confirm_password': 'NewPassword123'
            }
        )

        response = client.get(
            f'/reset-password/{token}',
            follow_redirects=True
        )

        assert response.status_code == 200

        with app.app_context():
            account_token = AccountToken.query.filter_by(
                user_id=user_id,
                purpose='password_reset'
            ).first()

            assert account_token.used_at is not None

    finally:
        cleanup([user_id])