# manage.py
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import create_app
from extension import db
from models import *

app = create_app()

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize Flask-Script Manager
manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
