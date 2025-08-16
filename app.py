from flask import Flask
from controllers.create_database_instance import create_tables
from controllers.database import db
from controllers.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    return app

app = create_app()

# Import routes after app creation to avoid circular imports
from controllers.general_routes import *

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True) 