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

    response = jsonify(data)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
