import os
import logging
import traceback
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

def create_app():
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
    app = Flask(__name__, static_folder=static_dir)

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e
        logging.error("Unhandled exception: %s", str(e))
        logging.error(traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    from src.routes.tasks import tasks_bp
    from src.routes.health import health_bp
    from src.routes.voice import voice_bp

    app.register_blueprint(tasks_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(voice_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=3000)
