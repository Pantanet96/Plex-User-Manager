"""
Standalone database initialization script
Creates database and default users without running the Flask app
"""
from database import db
from models import User
from flask import Flask
import os

def init_db_standalone():
    # Create minimal Flask app for database context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plex_manager.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Create default users if they don't exist
        users_created = []
        
        # Admin user
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role=User.ROLE_ADMIN)
            admin.set_password('Admin123!')
            db.session.add(admin)
            users_created.append('admin (role: admin, password: Admin123!)')
        
        # Moderator user
        if not User.query.filter_by(username='moderator').first():
            moderator = User(username='moderator', role=User.ROLE_MODERATOR)
            moderator.set_password('Mod123!')
            db.session.add(moderator)
            users_created.append('moderator (role: moderator, password: Mod123!)')
        
        # Auditor user
        if not User.query.filter_by(username='auditor').first():
            auditor = User(username='auditor', role=User.ROLE_AUDITOR)
            auditor.set_password('Audit123!')
            db.session.add(auditor)
            users_created.append('auditor (role: auditor, password: Audit123!)')
        
        if users_created:
            db.session.commit()
            print("✓ Database initialized successfully!")
            print("\nCreated default users:")
            for user in users_created:
                print(f"  - {user}")
            print("\n⚠️  IMPORTANT: Change these default passwords immediately!")
        else:
            print("Database already initialized. All default users exist.")

if __name__ == '__main__':
    init_db_standalone()
