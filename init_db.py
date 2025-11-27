from app import app
from database import db
from models import User

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role=User.ROLE_ADMIN)
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Database initialized. Created default admin user:")
            print("  - Username: admin")
            print("  - Password: admin")
            print("  - Role: admin")
            print("\n⚠️  IMPORTANT: Change the default password immediately!")
        else:
            print("Database already initialized. Admin user exists.")


if __name__ == '__main__':
    init_db()
