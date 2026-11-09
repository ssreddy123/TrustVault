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

from datetime import datetime

import os
import zipfile
import uuid


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


# ==========================================
# USER LOADER
# ==========================================

@login_manager.user_loader
def load_user(user_id):

    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


# ==========================================
# AUDIT LOG FUNCTION
# ==========================================

def log_action(action, details=''):

    db.session.add(AuditLog(
        user_id=current_user.id,
        action=action,
        details=details
    ))


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

    # PDF validation
    if extension == 'pdf':

        return header.startswith(b'%PDF-')

    # PNG validation
    if extension == 'png':

        return header.startswith(
            b'\x89PNG\r\n\x1a\n'
        )

    # JPG and JPEG validation
    if extension in ('jpg', 'jpeg'):

        return header.startswith(b'\xff\xd8\xff')

    # TXT validation
    if extension == 'txt':

        return b'\x00' not in header

    # DOCX validation
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

    # Edit permission also allows read access.
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

        password = request.form.get(
            'password', ''
        )

        if not username or len(password) < 8:

            flash(
                'Enter a username and password with at least 8 characters.'
            )

            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():

            flash('Username already exists.')

            return redirect(url_for('register'))

        user = User(
            username=username,
            password=generate_password_hash(password)
        )

        db.session.add(user)

        db.session.commit()

        flash('Registration successful. Please login.')

        return redirect(url_for('login'))

    return render_template('register.html')


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

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password, password
        ):

            login_user(user)

            return redirect(url_for('dashboard'))

        flash('Invalid username or password.')

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

    # Only administrators, owners and users
    # with Edit permission can replace documents.
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