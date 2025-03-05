from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify
from config import Config
import logging
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.directors import director_bp
    from app.routes.movies import movie_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(director_bp)
    app.register_blueprint(movie_bp)

    # Setup logging
    log_filename = "api_logs.log"
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    def log_request_response(response):
        """Logs API request and response details."""

        # Check if request contains JSON data
        request_data = None
        if request.content_type == "application/json":
            try:
                request_data = request.get_json()
            except Exception:
                request_data = "Invalid JSON"

        # Check if response contains JSON data
        response_data = None
        try:
            response_data = response.get_json()
        except Exception:
            response_data = "Non-JSON response"

        log_message = (
            f"Time: {datetime.utcnow()} | "
            f"Method: {request.method} | "
            f"URL: {request.url} | "
            f"Request Data: {request_data} | "
            f"Response Status: {response.status_code} | "
            f"Response Data: {response_data}"
        )
        logging.info(log_message)
        return response

    @app.after_request
    def after_request(response):
        return log_request_response(response)

    return app
