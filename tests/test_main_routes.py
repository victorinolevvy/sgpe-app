import unittest
from flask import url_for
from sgpe import create_app, db

class MainRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get(url_for('main.home'))
        self.assertTrue('SGPE' in response.get_data(as_text=True))

    def test_register_and_login(self):
        # Test registration
        response = self.client.post(url_for('main.register'), data={
            'username': 'susan',
            'email': 'susan@example.com',
            'password': 'cat',
            'confirm_password': 'cat'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Conta criada para susan!' in response.data)

        # Test login
        response = self.client.post(url_for('main.login'), data={
            'email': 'susan@example.com',
            'password': 'cat'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Dashboard de Projetos' in response.data)

        # Test logout
        response = self.client.get(url_for('main.logout'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Sess\xc3\xa3o terminada com sucesso.' in response.data)
