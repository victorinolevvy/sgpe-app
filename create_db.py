from sgpe import create_app, db

app = create_app('development')

with app.app_context():
    print("A apagar todas as tabelas da base de dados...")
    db.drop_all()
    print("A criar todas as tabelas da base de dados...")
    db.create_all()

print("Tabelas da base de dados recriadas com sucesso.")
