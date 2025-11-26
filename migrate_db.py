"""
Database migration script to add role column to User table
Run this script to migrate existing database to support RBAC
"""
import sqlite3
import os

def migrate_database():
    # Database is in instance folder
    db_path = os.path.join('instance', 'plex_manager.db')
    print(f"Target database: {os.path.abspath(db_path)}")
    
    if not os.path.exists(db_path):
        print("Database file not found. No migration needed.")
        return
    
    print("Starting database migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if role column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'role' in columns:
            print("Role column already exists. Migration not needed.")
            return
        
        # Add role column with default value 'auditor'
        print("Adding 'role' column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'auditor'")
        
        # Update existing admin user to have admin role
        print("Setting existing admin user to 'admin' role...")
        cursor.execute("UPDATE user SET role = 'admin' WHERE username = 'admin'")
        
        # Commit changes
        conn.commit()
        print("✓ Migration completed successfully!")
        print(f"  - Added 'role' column to user table")
        print(f"  - Set admin user role to 'admin'")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
