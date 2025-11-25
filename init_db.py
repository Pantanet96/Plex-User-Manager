from app import app
from database import db
from models import User

def init_db():
    with app.app_context():
        db.create_all()
        
        # Check if admin exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Database initialized and admin user created.")
        else:
            print("Database already initialized.")

if __name__ == '__main__':
    init_db()
