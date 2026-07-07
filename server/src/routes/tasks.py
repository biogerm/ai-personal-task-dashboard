from flask import Blueprint, jsonify, current_app


tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/api/tasks")
def get_tasks():
    try:
        from src.app import merger

        data = merger.get_data()
    except Exception:
        try:
            from app import merger

            data = merger.get_data()
        except Exception:
            data = current_app.merger.get_data()

    from src.utils.i18n import get_locale

    data["locale"] = get_locale()

    try:
        from src.utils.config import load_config

        config = load_config()
        data["carousel"] = config.get(
            "carousel", {"intervalSeconds": 300, "screens": [0, 1]}
        )
    except Exception:
        data["carousel"] = {"intervalSeconds": 300, "screens": [0, 1]}

    response = jsonify(data)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
