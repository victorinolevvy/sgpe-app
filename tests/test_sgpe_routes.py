import unittest
from flask import url_for
from sgpe import create_app, db
from sgpe.models import User, Supplier, ContractType

class SgpeRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)
        self.create_admin_user()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def create_admin_user(self):
        """Cria um utilizador administrador para os testes."""
        admin_user = User(username='admin', email='admin@test.com', password='adminpass', is_admin=True)
        db.session.add(admin_user)
        db.session.commit()

    def login_admin(self):
        """Faz login como o utilizador administrador."""
        return self.client.post(
            url_for('main.login'),
            data={'email': 'admin@test.com', 'password': 'adminpass'},
            follow_redirects=True
        )

    # ----- Testes de Fornecedores (Suppliers) -----

    def test_add_supplier(self):
        """Testa a adição de um novo fornecedor."""
        self.login_admin()
        response = self.client.post(url_for('main.add_supplier'), data={
            'name': 'Fornecedor Teste',
            'contact_person': 'John Doe',
            'email': 'john.doe@fornecedor.com',
            'phone': '123456789'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Fornecedor adicionado com sucesso!', response.data)
        supplier = Supplier.query.filter_by(name='Fornecedor Teste').first()
        self.assertIsNotNone(supplier)
        self.assertEqual(supplier.email, 'john.doe@fornecedor.com')

    def test_add_duplicate_supplier(self):
        """Testa a não adição de um fornecedor com nome duplicado."""
        self.login_admin()
        # Adiciona o primeiro fornecedor
        self.client.post(url_for('main.add_supplier'), data={'name': 'Duplicado'}, follow_redirects=True)
        # Tenta adicionar o segundo com o mesmo nome (case-insensitive)
        response = self.client.post(url_for('main.add_supplier'), data={'name': 'duplicado'}, follow_redirects=True)
        self.assertIn(b'Este nome de fornecedor j\xc3\xa1 existe.', response.data)

    # ----- Testes de Tipos de Contrato (Contract Types) -----

    def test_add_contract_type(self):
        """Testa a adição de um novo tipo de contrato."""
        self.login_admin()
        response = self.client.post(url_for('main.new_contract_type'), data={
            'name': 'Tipo Teste',
            'description': 'Descrição do tipo teste'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tipo de contrato criado com sucesso!', response.data)
        contract_type = ContractType.query.filter_by(name='Tipo Teste').first()
        self.assertIsNotNone(contract_type)
        self.assertEqual(contract_type.description, 'Descrição do tipo teste')

    def test_add_duplicate_contract_type(self):
        """Testa a não adição de um tipo de contrato com nome duplicado."""
        self.login_admin()
        # Adiciona o primeiro tipo
        self.client.post(url_for('main.new_contract_type'), data={'name': 'Tipo Duplicado'}, follow_redirects=True)
        # Tenta adicionar o segundo com o mesmo nome (case-insensitive)
        response = self.client.post(url_for('main.new_contract_type'), data={'name': 'tipo duplicado'}, follow_redirects=True)
        self.assertIn(b'Este nome de tipo de contrato j\xc3\xa1 existe.', response.data)
