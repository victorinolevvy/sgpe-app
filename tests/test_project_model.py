import unittest
from sgpe.models import Project, User, ProjectType
from sgpe import create_app, db

class ProjectModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_project(self):
        # Crie um usuário e um tipo de projeto primeiro
        user = User(username='testuser', email='test@example.com', password='cat')
        project_type = ProjectType(name='Test Type', description='A test type')
        db.session.add(user)
        db.session.add(project_type)
        db.session.commit()

        # Crie o projeto associado ao usuário e ao tipo de projeto
        p = Project(name='Test Project',
                    description='Test Description',
                    project_type_id=project_type.id,
                    location_province='Maputo',
                    location_district='Boane',
                    location_admin_post='Boane',
                    author=user)
        
        db.session.add(p)
        db.session.commit()

        # Verifique se o projeto foi criado corretamente
        self.assertTrue(p.id is not None)
        self.assertEqual(p.name, 'Test Project')
        self.assertEqual(p.author, user)
        self.assertEqual(p.project_type, project_type)
