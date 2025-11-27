from database import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    # Role constants
    ROLE_ADMIN = 'admin'
    ROLE_MODERATOR = 'moderator'
    ROLE_AUDITOR = 'auditor'
    ROLES = [ROLE_ADMIN, ROLE_MODERATOR, ROLE_AUDITOR]
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default=ROLE_AUDITOR)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        """Check if user has a specific role"""
        return self.role == role
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == self.ROLE_ADMIN
    
    def is_moderator(self):
        """Check if user is a moderator or admin"""
        return self.role in [self.ROLE_ADMIN, self.ROLE_MODERATOR]
    
    def is_auditor(self):
        """Check if user is an auditor (all authenticated users)"""
        return self.role in self.ROLES
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.is_admin()
    
    def can_edit_libraries(self):
        """Check if user can edit library access"""
        return self.is_moderator()
    
    def can_sync_plex(self):
        """Check if user can sync with Plex"""
        return self.is_moderator()
    
    def can_edit_settings(self):
        """Check if user can edit application settings"""
        return self.is_admin()

class PlexUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plex_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    thumb = db.Column(db.String(255))

class Library(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plex_key = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))

class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plex_user_id = db.Column(db.Integer, db.ForeignKey('plex_user.id'), nullable=False)
    library_id = db.Column(db.Integer, db.ForeignKey('library.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=True)
    expiration_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    plex_user = db.relationship('PlexUser', backref=db.backref('shares', lazy=True))
    library = db.relationship('Library', backref=db.backref('shares', lazy=True))

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255))

