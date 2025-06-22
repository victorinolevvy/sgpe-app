import unittest
from sgpe.models import Project, User
from sgpe import db
from datetime import datetime

class ProjectModelTestCase(unittest.TestCase):
    def test_create_project(self):
        u = User(username='testuser', email='test@example.com', password='cat')
        p = Project(name='Test Project',
                    description='Test Description',
                    location_province='Maputo',
                    location_district='Boane',
                    location_admin_post='Boane',
                    generation_capacity_kW=100,
                    storage_capacity_kWh=200,
                    network_type='MT/BT',
                    num_connections=50,
                    author=u)
        self.assertTrue(p.name == 'Test Project')
        self.assertTrue(p.author == u)
