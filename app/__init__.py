from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = "super_tajne_haslo_123"  # ← to dodaj

    from app.controllers.main_controller import main
    app.register_blueprint(main)

    return app
