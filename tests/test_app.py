import unittest
import os
import shutil
import yaml
import bcrypt
from app import app
from flask import session

class RPSTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'a_test_secret_key'
        self.client = app.test_client()

        self.test_dir = os.path.dirname(__file__)
        os.makedirs(self.test_dir, exist_ok=True)

        password = b'password'
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        test_user_data = {
            'testuser': {
                'password': hashed_password,
                'wins': 1,
                'losses': 1,
                'Raptor': 5,
                'Pterodactyl': 5,
                'Stegosaurus': 5
            }
        }

        with open(os.path.join(self.test_dir, 'users.yaml'), 'w') as f:
            yaml.dump(test_user_data, f)

    def tearDown(self):
        user_file_path = os.path.join(self.test_dir, 'users.yaml')
        if os.path.exists(user_file_path):
            os.remove(user_file_path)

# Helper method to sign in a user
    def sign_in(self, username, password):
        return self.client.post('/users/signin', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_index_page_requires_signin(self):
        """Test that accessing the root redirects to sign-in page if not logged in."""
        response = self.client.get('/')
        # 302 is the status code for a redirect
        self.assertEqual(response.status_code, 302)
        # Check that it redirects to the signin URL
        self.assertIn('/users/signin', response.location)

    def test_successful_signin(self):
        """Test that a user can sign in successfully."""
        with self.client as client:
            response = self.sign_in('testuser', 'password')

            # After successful sign-in, should be on the game page
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Welcome to Raptor, Pterodactyl, Stegosaurus!', response.data)

            # Check that the username is in the session
            self.assertEqual(session.get('username'), 'testuser')

    def test_play_round_updates_stats_file(self):
        """Test that playing a round correctly updates the users.yaml file."""
        with self.client as client:
            # First, sign in the test user
            self.sign_in('testuser', 'password')

            # Then, simulate playing a round by choosing 'Raptor'
            client.post('/', data={'move': 'Raptor'})

            # Now, check if the yaml file was updated
            user_data_path = os.path.join(self.test_dir, 'users.yaml')
            with open(user_data_path, 'r') as f:
                users = yaml.safe_load(f)

            # The 'Raptor' count for 'testuser' should have increased from 5 to 6
            self.assertEqual(users['testuser']['Raptor'], 6)

if __name__ == '__main__':
    unittest.main()