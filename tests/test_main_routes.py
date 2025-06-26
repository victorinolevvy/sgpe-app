import unittest
from flask import url_for
from sgpe import create_app, db
from sgpe.models import User, Project, ProjectType

class MainRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)
        self.create_test_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def create_test_data(self):
        # Criar utilizador admin
        admin_user = User(username='admin', email='admin@test.com', password='adminpass', is_admin=True)
        db.session.add(admin_user)
        # Criar tipo de projeto
        project_type = ProjectType(name='Test Type', description='A test type')
        db.session.add(project_type)
        db.session.commit()

    def login_admin(self):
        return self.client.post(
            url_for('main.login'),
            data={'email': 'admin@test.com', 'password': 'adminpass'},
            follow_redirects=True
        )

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
        self.assertIn(b'<h1>Dashboard</h1>', response.data)

        # Test logout
        response = self.client.get(url_for('main.logout'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sess\xc3\xa3o terminada com sucesso.', response.data)

    def test_create_project(self):
        self.login_admin()
        project_type = ProjectType.query.first()
        response = self.client.post(url_for('main.new_project'), data={
            'name': 'New Test Project',
            'project_type_id': project_type.id,
            'location_province': 'Maputo Província',
            'location_district': 'Boane',
            'location_admin_post': 'Boane'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Projeto criado com sucesso!', response.data)
        # Verificar se o projeto está no dashboard
        self.assertIn(b'New Test Project', response.data)
        self.assertIn(b'Test Type', response.data) # Verificar o tipo de projeto

    def test_update_project(self):
        self.login_admin()
        project_type = ProjectType.query.first()
        user = User.query.filter_by(username='admin').first()
        project = Project(
            name='Project to Update',
            project_type_id=project_type.id,
            location_province='Gaza',
            location_district='Chibuto',
            location_admin_post='Chibuto',
            author=user
        )
        db.session.add(project)
        db.session.commit()

        response = self.client.post(url_for('main.update_project', project_id=project.id), data={
            'name': 'Updated Project Name',
            'project_type_id': project_type.id,
            'location_province': 'Inhambane',
            'location_district': 'Maxixe',
            'location_admin_post': 'Maxixe'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'O projeto foi atualizado com sucesso!', response.data)
        # Verificar se os detalhes atualizados estão na página do projeto
        self.assertIn(b'Updated Project Name', response.data)
        self.assertIn(b'Inhambane', response.data)

    def test_delete_project(self):
        self.login_admin()
        project_type = ProjectType.query.first()
        user = User.query.filter_by(username='admin').first()
        project = Project(
            name='Project to Delete',
            project_type_id=project_type.id,
            location_province='Sofala',
            location_district='Beira',
            location_admin_post='Beira',
            author=user
        )
        db.session.add(project)
        db.session.commit()

        response = self.client.post(url_for('main.delete_project', project_id=project.id), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'O seu projeto foi apagado!', response.data)
        self.assertNotIn(b'Project to Delete', response.data)
