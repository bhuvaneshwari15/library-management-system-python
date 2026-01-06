# type: ignore
# pyright: ignore
from app import create_app
from extension import db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

if __name__ == "__main__":
    app.run(debug=True)
