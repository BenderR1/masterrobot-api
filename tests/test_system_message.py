# tests/test_system_message.py
import unittest
import json
from app import create_app
from app.config import TestConfig
from app.services import db_service
from app.services import auth_service # To help with login/tokens

class SystemMessageTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and initialize test database."""
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db_service.init_db() # Initialize schema in test context

        # Register and log in a test user to get a token
        auth_service.register_user('testuser', 'password')
        login_resp = self.client.post('/api/v1/auth/login', json={'username': 'testuser', 'password': 'password'})
        self.access_token = json.loads(login_resp.data)['access_token']
        self.auth_headers = {'Authorization': f'Bearer {self.access_token}'}


    def tearDown(self):
        """Clean up database and app context."""
        self.app_context.pop()

    def test_create_and_list_system_message(self):
        # 1. Create a message
        create_resp = self.client.post('/api/v1/system_message/', headers=self.auth_headers, json={
            'name': 'Test Prompt',
            'content': 'You are a test assistant.'
        })
        self.assertEqual(create_resp.status_code, 201)
        created_data = json.loads(create_resp.data)
        self.assertEqual(created_data['name'], 'Test Prompt')
        self.assertIn('id', created_data)
        message_id = created_data['id']

        # 2. List messages
        list_resp = self.client.get('/api/v1/system_message/', headers=self.auth_headers)
        self.assertEqual(list_resp.status_code, 200)
        list_data = json.loads(list_resp.data)
        self.assertEqual(len(list_data), 1)
        self.assertEqual(list_data[0]['name'], 'Test Prompt')
        self.assertEqual(list_data[0]['id'], message_id)

    def test_get_system_message(self):
        # Create first
        create_resp = self.client.post('/api/v1/system_message/', headers=self.auth_headers, json={'name': 'Get Me', 'content': 'Details'})
        message_id = json.loads(create_resp.data)['id']

        # Get it
        get_resp = self.client.get(f'/api/v1/system_message/{message_id}', headers=self.auth_headers)
        self.assertEqual(get_resp.status_code, 200)
        get_data = json.loads(get_resp.data)
        self.assertEqual(get_data['name'], 'Get Me')

    def test_update_system_message(self):
        # Create first
        create_resp = self.client.post('/api/v1/system_message/', headers=self.auth_headers, json={'name': 'Update Me', 'content': 'Old Content'})
        message_id = json.loads(create_resp.data)['id']

        # Update it
        update_resp = self.client.put(f'/api/v1/system_message/{message_id}', headers=self.auth_headers, json={
            'name': 'Updated Name',
            'content': 'New Content'
        })
        self.assertEqual(update_resp.status_code, 200)
        update_data = json.loads(update_resp.data)
        self.assertEqual(update_data['name'], 'Updated Name')
        self.assertEqual(update_data['content'], 'New Content')

        # Verify update with a GET
        get_resp = self.client.get(f'/api/v1/system_message/{message_id}', headers=self.auth_headers)
        get_data = json.loads(get_resp.data)
        self.assertEqual(get_data['name'], 'Updated Name')


    def test_delete_system_message(self):
         # Create first
        create_resp = self.client.post('/api/v1/system_message/', headers=self.auth_headers, json={'name': 'Delete Me', 'content': 'Gone'})
        message_id = json.loads(create_resp.data)['id']

        # Delete it
        delete_resp = self.client.delete(f'/api/v1/system_message/{message_id}', headers=self.auth_headers)
        self.assertEqual(delete_resp.status_code, 200) # Or 204 if you change the route

        # Verify deletion with a GET (should be 404)
        get_resp = self.client.get(f'/api/v1/system_message/{message_id}', headers=self.auth_headers)
        self.assertEqual(get_resp.status_code, 404)

    # Add tests for error conditions (unauthorized, bad input, not found, duplicates etc.)

if __name__ == '__main__':
    unittest.main()