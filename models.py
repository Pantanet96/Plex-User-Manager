from database import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

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

