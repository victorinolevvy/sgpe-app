import os
from sgpe import create_app, db

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
