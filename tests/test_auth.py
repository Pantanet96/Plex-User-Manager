"""
Unit tests for authentication and authorization
"""
import unittest
from app import app
from database import db
from models import User


class TestAuthentication(unittest.TestCase):
    """Test cases for authentication"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        user = User(username='testadmin', role=User.ROLE_ADMIN)
        user.set_password('admin')
        db.session.add(user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_login_page_loads(self):
        """Test that login page loads"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_successful_login(self):
        """Test successful login"""
        response = self.client.post('/login', data={
            'username': 'testadmin',
            'password': 'admin'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_failed_login(self):
        """Test failed login with wrong password"""
        response = self.client.post('/login', data={
            'username': 'testadmin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Should stay on login page or show error


class TestAuthorization(unittest.TestCase):
    """Test cases for role-based authorization"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test users with different roles
        admin = User(username='admin', role=User.ROLE_ADMIN)
        admin.set_password('admin')
        
        moderator = User(username='moderator', role=User.ROLE_MODERATOR)
        moderator.set_password('mod')
        
        auditor = User(username='auditor', role=User.ROLE_AUDITOR)
        auditor.set_password('audit')
        
        db.session.add_all([admin, moderator, auditor])
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, username, password):
        """Helper method to login"""
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    
    def test_admin_access_to_users(self):
        """Test that admin can access user management"""
        self.login('admin', 'admin')
        response = self.client.get('/users')
        self.assertEqual(response.status_code, 200)
    
    def test_moderator_no_access_to_users(self):
        """Test that moderator cannot access user management"""
        self.login('moderator', 'mod')
        response = self.client.get('/users')
        # Should redirect or return 403
        self.assertIn(response.status_code, [302, 403])


if __name__ == '__main__':
    unittest.main()
