"""
Unit tests for database models
"""
import unittest
from app import app
from database import db
from models import User, PlexUser, Library, Share, Settings


class TestUserModel(unittest.TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_user_creation(self):
        """Test creating a new user"""
        user = User(username='testuser', role=User.ROLE_ADMIN)
        user.set_password('TestPassword123!')
        db.session.add(user)
        db.session.commit()
        
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, User.ROLE_ADMIN)
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        user = User(username='testuser', role=User.ROLE_ADMIN)
        password = 'SecurePassword123!'
        user.set_password(password)
        
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.check_password('WrongPassword'))
    
    def test_user_roles(self):
        """Test user role methods"""
        admin = User(username='admin', role=User.ROLE_ADMIN)
        moderator = User(username='mod', role=User.ROLE_MODERATOR)
        auditor = User(username='audit', role=User.ROLE_AUDITOR)
        
        self.assertTrue(admin.is_admin())
        self.assertTrue(admin.is_moderator())  # Admin has moderator privileges
        
        self.assertFalse(moderator.is_admin())
        self.assertTrue(moderator.is_moderator())
        
        self.assertFalse(auditor.is_admin())
        self.assertFalse(auditor.is_moderator())


class TestPlexUserModel(unittest.TestCase):
    """Test cases for PlexUser model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_plex_user_creation(self):
        """Test creating a Plex user"""
        plex_user = PlexUser(
            username='plexuser',
            email='user@example.com',
            plex_id='12345'
        )
        db.session.add(plex_user)
        db.session.commit()
        
        self.assertIsNotNone(plex_user.id)
        self.assertEqual(plex_user.username, 'plexuser')
        self.assertEqual(plex_user.plex_id, '12345')


if __name__ == '__main__':
    unittest.main()
