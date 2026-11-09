from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_from_directory
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)

from flask_wtf.csrf import CSRFProtect

from werkzeug.security import (
    generate_password_hash, check_password_hash
)

from werkzeug.utils import secure_filename

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import os
import zipfile
import uuid
import secrets
import hashlib
import smtplib


# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY environment variable is not set")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trustvault.db'

app.config['UPLOAD_FOLDER'] = os.path.join(
    app.instance_path, 'uploads'
)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True

os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

csrf = CSRFProtect(app)

db = SQLAlchemy(app)


# ==========================================
# LOGIN CONFIGURATION
# ==========================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'login'


# ==========================================
# ALLOWED FILE TYPES
# ==========================================

ALLOWED_EXTENSIONS = {
    'pdf', 'txt', 'docx', 'png', 'jpg', 'jpeg'
}


# ==========================================
# DATABASE MODELS
# ==========================================

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    email = db.Column(
        db.String(254),
        unique=True,
        nullable=True
    )

    email_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default='user'
    )


class Document(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(
        db.String(200),
        nullable=False
    )

    stored_name = db.Column(
        db.String(200),
        unique=True,
        nullable=False
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Permission(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    document_id = db.Column(
        db.Integer,
        db.ForeignKey('document.id'),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    access = db.Column(
        db.String(10),
        nullable=False
    )


class AuditLog(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        nullable=False
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    details = db.Column(
        db.String(300)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class AccountToken(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    token_hash = db.Column(
        db.String(64),
        unique=True,
        nullable=False
    )

    purpose = db.Column(
        db.String(30),
        nullable=False
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    used_at = db.Column(
        db.DateTime,
        nullable=True
    )


# ==========================================
# ACCOUNT SECURITY HELPERS
# ==========================================

def utc_now():

    return datetime.now(timezone.utc).replace(
        tzinfo=None
    )


def log_action(action, details=''):

    db.session.add(AuditLog(
        user_id=current_user.id,
        action=action,
        details=details
    ))


def log_account_action(user_id, action, details=''):

    db.session.add(AuditLog(
        user_id=user_id,
        action=action,
        details=details
    ))


def create_account_token(user, purpose):

    # Invalidate previous unused tokens of the same type.

    AccountToken.query.filter_by(
        user_id=user.id,
        purpose=purpose,
        used_at=None
    ).delete()

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()

    token = AccountToken(
        user_id=user.id,
        token_hash=token_hash,
        purpose=purpose,
        expires_at=utc_now() + timedelta(minutes=15)
    )

    db.session.add(token)

    db.session.commit()

    return raw_token


def get_valid_account_token(raw_token, purpose):

    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()

    token = AccountToken.query.filter_by(
        token_hash=token_hash,
        purpose=purpose,
        used_at=None
    ).first()

    if not token:
        return None

    if token.expires_at <= utc_now():
        return None

    return token


# ==========================================
# EMAIL CONFIGURATION
# ==========================================

def send_email(recipient, subject, body):

    host = os.environ.get('SMTP_HOST')

    port = int(
        os.environ.get('SMTP_PORT', '587')
    )

    username = os.environ.get('SMTP_USERNAME')

    password = os.environ.get('SMTP_PASSWORD')

    sender = os.environ.get('MAIL_FROM') or username

    if not all([host, username, password, sender]):

        raise RuntimeError(
            "SMTP configuration is incomplete"
        )

    message = EmailMessage()

    message['Subject'] = subject

    message['From'] = sender

    message['To'] = recipient

    message.set_content(body)

    if port == 465:

        with smtplib.SMTP_SSL(
            host, port, timeout=15
        ) as server:

            server.login(username, password)

            server.send_message(message)

    else:

        with smtplib.SMTP(
            host, port, timeout=15
        ) as server:

            server.ehlo()

            server.starttls()

            server.ehlo()

            server.login(username, password)

            server.send_message(message)


def send_account_link(user, purpose):

    raw_token = create_account_token(
        user, purpose
    )

    if purpose == 'verify_email':

        endpoint = 'verify_email'

        subject = 'Verify your TrustVault email'

        message = 'Click this link to verify your email:'

    else:

        endpoint = 'reset_password'

        subject = 'TrustVault password reset'

        message = 'Click this link to reset your password:'

    link = url_for(
        endpoint,
        token=raw_token,
        _external=True
    )

    send_email(
        user.email,
        subject,
        f'{message}\n\n{link}\n\n'
        'This link expires in 15 minutes. '
        'If you did not request this, ignore this email.'
    )


# ==========================================
# USER LOADER
# ==========================================

@login_manager.user_loader
def load_user(user_id):

    try:

        return db.session.get(
            User, int(user_id)
        )

    except (ValueError, TypeError):

        return None


# ==========================================
# FILE VALIDATION
# ==========================================

def allowed_file(file):

    filename = secure_filename(file.filename)

    if not filename or '.' not in filename:

        return False

    extension = filename.rsplit('.', 1)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:

        return False

    file.stream.seek(0)

    header = file.stream.read(16)

    file.stream.seek(0)

    if extension == 'pdf':

        return header.startswith(b'%PDF-')

    if extension == 'png':

        return header.startswith(b'\x89PNG\r\n\x1a\n')

    if extension in ('jpg', 'jpeg'):

        return header.startswith(b'\xff\xd8\xff')

    if extension == 'txt':

        return b'\x00' not in header

    if extension == 'docx':

        try:

            with zipfile.ZipFile(file.stream) as archive:

                names = archive.namelist()

                valid = (
                    '[Content_Types].xml' in names
                    and 'word/document.xml' in names
                )

                file.stream.seek(0)

                return valid

        except zipfile.BadZipFile:

            file.stream.seek(0)

            return False

    return False


# ==========================================
# ACCESS CONTROL
# ==========================================

def can_access(document, permission='read'):

    if (
        current_user.role == 'admin'
        or document.owner_id == current_user.id
    ):

        return True

    access = Permission.query.filter_by(
        document_id=document.id,
        user_id=current_user.id
    ).first()

    if not access:

        return False

    if permission == 'read':

        return access.access in {'read', 'edit'}

    if permission == 'edit':

        return access.access == 'edit'

    return False


# ==========================================
# HOME ROUTE
# ==========================================

@app.route('/')
def home():

    if current_user.is_authenticated:

        return redirect(url_for('dashboard'))

    return redirect(url_for('login'))


# ==========================================
# REGISTER
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form.get(
            'username', ''
        ).strip()

        email = request.form.get(
            'email', ''
        ).strip().lower()

        password = request.form.get(
            'password', ''
        )

        if not username or len(password) < 8:

            flash(
                'Enter a username and password '
                'with at least 8 characters.'
            )

            return redirect(url_for('register'))

        if (
            len(email) > 254
            or '@' not in email
            or email.count('@') != 1
            or '.' not in email.split('@')[-1]
        ):

            flash('Enter a valid email address.')

            return redirect(url_for('register'))

        if User.query.filter_by(
            username=username
        ).first():

            flash('Username already exists.')

            return redirect(url_for('register'))

        if User.query.filter_by(
            email=email
        ).first():

            flash('Email address already registered.')

            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            email_verified=False,
            password=generate_password_hash(password),
            role='user'
        )

        db.session.add(user)

        db.session.commit()

        try:

            send_account_link(
                user, 'verify_email'
            )

        except Exception:

            app.logger.exception(
                'Registration verification email failed'
            )

            flash(
                'Account created, but verification email '
                'could not be sent. Configure SMTP and '
                'use Resend Verification.'
            )

            return redirect(
                url_for('resend_verification')
            )

        flash(
            'Registration successful. '
            'Check your email to verify your account.'
        )

        return redirect(url_for('login'))

    return render_template('register.html')


# ==========================================
# EMAIL VERIFICATION
# ==========================================

@app.route('/verify-email/<token>')
def verify_email(token):

    account_token = get_valid_account_token(
        token, 'verify_email'
    )

    if not account_token:

        flash(
            'Verification link is invalid or expired.'
        )

        return redirect(url_for('login'))

    user = db.session.get(
        User, account_token.user_id
    )

    if not user:

        flash('Account not found.')

        return redirect(url_for('login'))

    user.email_verified = True

    account_token.used_at = utc_now()

    log_account_action(
        user.id,
        'EMAIL_VERIFIED',
        'Email address verified successfully'
    )

    db.session.commit()

    flash(
        'Email verified successfully. You can now login.'
    )

    return redirect(url_for('login'))


# ==========================================
# RESEND VERIFICATION
# ==========================================

@app.route(
    '/resend-verification',
    methods=['GET', 'POST']
)
def resend_verification():

    if request.method == 'POST':

        email = request.form.get(
            'email', ''
        ).strip().lower()

        user = User.query.filter_by(
            email=email
        ).first()

        if user and not user.email_verified:

            try:

                send_account_link(
                    user, 'verify_email'
                )

            except Exception:

                app.logger.exception(
                    'Verification email resend failed'
                )

        flash(
            'If an unverified account exists for that '
            'email, a verification link will be sent.'
        )

        return redirect(
            url_for('login')
        )

    return render_template(
        'resend_verification.html'
    )


# ==========================================
# FORGOT PASSWORD
# ==========================================

@app.route(
    '/forgot-password',
    methods=['GET', 'POST']
)
def forgot_password():

    if request.method == 'POST':

        email = request.form.get(
            'email', ''
        ).strip().lower()

        user = User.query.filter_by(
            email=email,
            email_verified=True
        ).first()

        if user:

            try:

                send_account_link(
                    user, 'password_reset'
                )

                log_account_action(
                    user.id,
                    'PASSWORD_RESET_REQUEST',
                    'Password reset requested'
                )

                db.session.commit()

            except Exception:

                db.session.rollback()

                app.logger.exception(
                    'Password reset email failed'
                )

        flash(
            'If a verified account exists for that email, '
            'a password reset link will be sent.'
        )

        return redirect(
            url_for('login')
        )

    return render_template(
        'forgot_password.html'
    )


# ==========================================
# RESET PASSWORD
# ==========================================

@app.route(
    '/reset-password/<token>',
    methods=['GET', 'POST']
)
def reset_password(token):

    account_token = get_valid_account_token(
        token, 'password_reset'
    )

    if not account_token:

        flash(
            'Password reset link is invalid or expired.'
        )

        return redirect(url_for('forgot_password'))

    user = db.session.get(
        User, account_token.user_id
    )

    if not user:

        flash('Account not found.')

        return redirect(url_for('forgot_password'))

    if request.method == 'POST':

        password = request.form.get(
            'password', ''
        )

        confirm_password = request.form.get(
            'confirm_password', ''
        )

        if len(password) < 8:

            flash(
                'Password must contain at least 8 characters.'
            )

            return redirect(
                url_for(
                    'reset_password',
                    token=token
                )
            )

        if password != confirm_password:

            flash('Passwords do not match.')

            return redirect(
                url_for(
                    'reset_password',
                    token=token
                )
            )

        user.password = generate_password_hash(
            password
        )

        account_token.used_at = utc_now()

        # Invalidate all other outstanding reset tokens.

        AccountToken.query.filter_by(
            user_id=user.id,
            purpose='password_reset',
            used_at=None
        ).update({
            'used_at': utc_now()
        })

        log_account_action(
            user.id,
            'PASSWORD_RESET_SUCCESS',
            'Password successfully reset'
        )

        db.session.commit()

        flash(
            'Password changed successfully. Please login.'
        )

        return redirect(url_for('login'))

    return render_template(
        'reset_password.html'
    )


# ==========================================
# ACCOUNT EMAIL MANAGEMENT
# ==========================================

@app.route(
    '/account/email',
    methods=['GET', 'POST']
)
@login_required
def account_email():

    if request.method == 'POST':

        email = request.form.get(
            'email', ''
        ).strip().lower()

        if (
            len(email) > 254
            or '@' not in email
            or email.count('@') != 1
            or '.' not in email.split('@')[-1]
        ):

            flash('Enter a valid email address.')

            return redirect(
                url_for('account_email')
            )

        existing = User.query.filter_by(
            email=email
        ).first()

        if existing and existing.id != current_user.id:

            flash('This email is already registered.')

            return redirect(
                url_for('account_email')
            )

        current_user.email = email

        current_user.email_verified = False

        db.session.commit()

        try:

            send_account_link(
                current_user, 'verify_email'
            )

        except Exception:

            app.logger.exception(
                'Account email verification failed'
            )

            flash(
                'Email saved, but verification email could '
                'not be sent. Check SMTP settings.'
            )

            return redirect(
                url_for('account_email')
            )

        flash(
            'Verification link sent. Check your email.'
        )

        return redirect(
            url_for('account_email')
        )

    return render_template(
        'account_email.html'
    )


# ==========================================
# LOGIN
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get(
            'username', ''
        ).strip()

        password = request.form.get(
            'password', ''
        )

        selected_role = request.form.get(
            'selected_role', ''
        ).strip().lower()

        if selected_role not in {
            'admin', 'owner', 'viewer'
        }:

            flash('Please select a valid login type.')

            return redirect(url_for('login'))

        user = User.query.filter_by(
            username=username
        ).first()

        if not user or not check_password_hash(
            user.password, password
        ):

            flash('Invalid username or password.')

            return redirect(url_for('login'))

        # Existing accounts with no email remain usable.
        # Accounts with an unverified email cannot log in.

        if user.email and not user.email_verified:

            flash(
                'Please verify your email before logging in.'
            )

            return redirect(
                url_for('resend_verification')
            )

        if selected_role == 'admin':

            if user.role != 'admin':

                flash(
                    'This account is not an administrator. '
                    'Please use the correct login option.'
                )

                return redirect(url_for('login'))

        elif selected_role == 'owner':

            if user.role == 'admin':

                flash(
                    'Please use Administrator Login '
                    'for this account.'
                )

                return redirect(url_for('login'))

        elif selected_role == 'viewer':

            if user.role == 'admin':

                flash(
                    'Please use Administrator Login '
                    'for this account.'
                )

                return redirect(url_for('login'))

        login_user(user)

        flash('Login successful.')

        return redirect(url_for('dashboard'))

    return render_template('login.html')


# ==========================================
# LOGOUT
# ==========================================

@app.route('/logout', methods=['POST'])
@login_required
def logout():

    logout_user()

    return redirect(url_for('login'))


# ==========================================
# DASHBOARD
# ==========================================

@app.route('/dashboard')
@login_required
def dashboard():

    documents = Document.query.all()

    visible_documents = [
        doc for doc in documents
        if can_access(doc)
    ]

    logs = AuditLog.query.filter_by(
        user_id=current_user.id
    ).order_by(
        AuditLog.created_at.desc()
    ).limit(10).all()

    permissions = {}

    can_edit = {}

    for doc in visible_documents:

        can_edit[doc.id] = can_access(
            doc, 'edit'
        )

        if doc.owner_id == current_user.id:

            permissions[doc.id] = Permission.query.filter_by(
                document_id=doc.id
            ).all()

    return render_template(
        'dashboard.html',
        documents=visible_documents,
        logs=logs,
        permissions=permissions,
        can_edit=can_edit
    )


# ==========================================
# UPLOAD DOCUMENT
# ==========================================

@app.route('/upload', methods=['POST'])
@login_required
def upload():

    file = request.files.get('file')

    if not file or not file.filename:

        flash('Select a file.')

        return redirect(url_for('dashboard'))

    original_name = secure_filename(file.filename)

    if not original_name or not allowed_file(file):

        flash('Invalid or unsupported file.')

        return redirect(url_for('dashboard'))

    stored_name = f'{uuid.uuid4().hex}_{original_name}'

    file_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        stored_name
    )

    file.save(file_path)

    document = Document(
        filename=original_name,
        stored_name=stored_name,
        owner_id=current_user.id
    )

    db.session.add(document)

    db.session.flush()

    log_action(
        'UPLOAD',
        f'Uploaded {original_name}'
    )

    db.session.commit()

    flash('Document uploaded successfully.')

    return redirect(url_for('dashboard'))


# ==========================================
# REPLACE DOCUMENT
# ==========================================

@app.route('/replace/<int:doc_id>', methods=['POST'])
@login_required
def replace_document(doc_id):

    document = db.session.get(
        Document, doc_id
    )

    if not document:

        return 'Document not found', 404

    if not can_access(document, 'edit'):

        log_action(
            'ACCESS_DENIED',
            f'Denied replace attempt for document {doc_id}'
        )

        db.session.commit()

        return 'Access denied', 403

    file = request.files.get('file')

    if not file or not file.filename:

        flash('Select a replacement file.')

        return redirect(url_for('dashboard'))

    original_name = secure_filename(file.filename)

    if not original_name or not allowed_file(file):

        flash('Invalid or unsupported file.')

        return redirect(url_for('dashboard'))

    new_stored_name = f'{uuid.uuid4().hex}_{original_name}'

    new_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        new_stored_name
    )

    old_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        document.stored_name
    )

    file.save(new_path)

    document.stored_name = new_stored_name

    document.filename = original_name

    log_action(
        'REPLACE',
        f'Replaced document {document.id}'
    )

    db.session.commit()

    if os.path.isfile(old_path):

        os.remove(old_path)

    flash('Document updated successfully.')

    return redirect(url_for('dashboard'))


# ==========================================
# SHARE DOCUMENT
# ==========================================

@app.route('/share/<int:doc_id>', methods=['POST'])
@login_required
def share(doc_id):

    document = db.session.get(
        Document, doc_id
    )

    if (
        not document
        or document.owner_id != current_user.id
    ):

        log_action(
            'ACCESS_DENIED',
            f'Denied share attempt for document {doc_id}'
        )

        db.session.commit()

        flash('Only the owner can share this document.')

        return redirect(url_for('dashboard'))

    username = request.form.get(
        'username', ''
    ).strip()

    access = request.form.get(
        'access', 'read'
    )

    if access not in {'read', 'edit'}:

        flash('Invalid permission.')

        return redirect(url_for('dashboard'))

    user = User.query.filter_by(
        username=username
    ).first()

    if not user or user.id == current_user.id:

        flash('Invalid recipient.')

        return redirect(url_for('dashboard'))

    permission = Permission.query.filter_by(
        document_id=doc_id,
        user_id=user.id
    ).first()

    if permission:

        permission.access = access

    else:

        db.session.add(Permission(
            document_id=doc_id,
            user_id=user.id,
            access=access
        ))

    log_action(
        'SHARE',
        f'Shared document {doc_id} with {username}'
    )

    db.session.commit()

    flash('Document shared successfully.')

    return redirect(url_for('dashboard'))


# ==========================================
# DELETE DOCUMENT (OWNER ONLY)
# ==========================================

@app.route('/delete/<int:doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):

    document = db.session.get(
        Document, doc_id
    )

    if (
        not document
        or document.owner_id != current_user.id
    ):

        log_action(
            'ACCESS_DENIED',
            f'Denied delete attempt for document {doc_id}'
        )

        db.session.commit()

        flash('Only the document owner can delete this document.')

        return redirect(url_for('dashboard'))

    file_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        document.stored_name
    )

    Permission.query.filter_by(
        document_id=doc_id
    ).delete()

    log_action(
        'DELETE',
        f'Deleted document {doc_id}: {document.filename}'
    )

    db.session.delete(document)

    db.session.commit()

    if os.path.isfile(file_path):

        os.remove(file_path)

    flash('Document deleted successfully.')

    return redirect(url_for('dashboard'))


# ==========================================
# REVOKE DOCUMENT ACCESS
# ==========================================

@app.route('/revoke/<int:doc_id>/<int:user_id>', methods=['POST'])
@login_required
def revoke(doc_id, user_id):

    document = db.session.get(
        Document, doc_id
    )

    if (
        not document
        or document.owner_id != current_user.id
    ):

        log_action(
            'ACCESS_DENIED',
            f'Denied revoke attempt for document {doc_id}'
        )

        db.session.commit()

        flash('Permission denied.')

        return redirect(url_for('dashboard'))

    permission = Permission.query.filter_by(
        document_id=doc_id,
        user_id=user_id
    ).first()

    if permission:

        db.session.delete(permission)

        log_action(
            'REVOKE',
            f'Revoked access to document {doc_id}'
        )

        db.session.commit()

        flash('Access revoked.')

    return redirect(url_for('dashboard'))


# ==========================================
# DOWNLOAD DOCUMENT
# ==========================================

@app.route('/download/<int:doc_id>')
@login_required
def download(doc_id):

    document = db.session.get(
        Document, doc_id
    )

    if not document or not can_access(document):

        log_action(
            'ACCESS_DENIED',
            f'Denied download attempt for document {doc_id}'
        )

        db.session.commit()

        return 'Access denied', 403

    log_action(
        'DOWNLOAD',
        f'Downloaded document {doc_id}'
    )

    db.session.commit()

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        document.stored_name,
        as_attachment=True,
        download_name=document.filename
    )


# ==========================================
# ADMIN AUDIT LOGS
# ==========================================

@app.route('/logs')
@login_required
def logs():

    if current_user.role != 'admin':

        return 'Access denied', 403

    all_logs = AuditLog.query.order_by(
        AuditLog.created_at.desc()
    ).all()

    users = {
        u.id: u.username
        for u in User.query.all()
    }

    return render_template(
        'dashboard.html',
        documents=[],
        logs=all_logs,
        permissions={},
        can_edit={},
        users=users
    )


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

with app.app_context():

    db.create_all()

    if not User.query.filter_by(
        username='admin'
    ).first():

        admin_password = os.environ.get(
            'ADMIN_PASSWORD'
        )

        if not admin_password:

            raise RuntimeError(
                "ADMIN_PASSWORD environment variable is required"
            )

        admin = User(
            username='admin',
            password=generate_password_hash(admin_password),
            role='admin'
        )

        db.session.add(admin)

        db.session.commit()


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == '__main__':

    app.run(debug=False)