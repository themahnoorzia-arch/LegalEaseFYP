from flask import Flask
from flask import send_from_directory

import os

from config import Config

from extensions import register_extensions

# --------------------------------------------------
# BLUEPRINTS
# --------------------------------------------------
from blueprints.auth import auth_bp
from blueprints.users import users_bp
from blueprints.court import court_bp
from blueprints.financials import financials_bp
from blueprints.legal_actors import legal_actors_bp
from blueprints.cases import cases_bp
from blueprints.registrar_routes import registrar_bp


def create_app():

    app = Flask(
        __name__,
        static_folder="../frontend/build",
        static_url_path=""
    )

    app.config.from_object(Config)

    register_extensions(app)

    # ----------------------------------------------
    # REGISTER BLUEPRINTS
    # ----------------------------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(court_bp)
    app.register_blueprint(financials_bp)
    app.register_blueprint(legal_actors_bp)
    app.register_blueprint(cases_bp)
    app.register_blueprint(registrar_bp, url_prefix='/api/registrar')

    # ----------------------------------------------
    # HEALTH CHECK
    # ----------------------------------------------
    @app.route("/health")
    def health():
        return {"status": "ok"}

    # ----------------------------------------------
    # REACT BUILD
    # ----------------------------------------------
    @app.route("/")
    def serve():
        return send_from_directory(
            app.static_folder,
            "index.html"
        )



    return app
app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )