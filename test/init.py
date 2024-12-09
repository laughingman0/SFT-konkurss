from flask import Flask
from .config import Config
from .routes import main_bp  # Importing the routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Load the config

    app.register_blueprint(main_bp)  # Register the routes/blueprints

    return app
