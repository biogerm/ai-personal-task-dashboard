import sys
import time
from flask import Blueprint, jsonify, current_app


health_bp = Blueprint("health", __name__)
START_TIME = time.time()


@health_bp.route("/api/health")
def get_health():
    try:
        from src.app import merger
        data = merger.get_data()
    except Exception:
        try:
            from app import merger
            data = merger.get_data()
        except Exception:
            try:
                data = current_app.merger.get_data()
            except Exception:
                data = {"sources": {}}

    sources = data.get("sources", {})
    source_statuses = [s.get("status") for s in sources.values()]

    is_all_ok = all(s == "ok" for s in source_statuses)
    is_all_err = all(s == "error" for s in source_statuses)

    if len(source_statuses) > 0 and is_all_ok:
        status = "ok"
    elif len(source_statuses) > 0 and is_all_err:
        status = "error"
    elif len(source_statuses) > 0:
        status = "degraded"
    else:
        status = "ok"

    response_data = {
        "status": status,
        "uptime_seconds": int(time.time() - START_TIME),
        "python_version": sys.version.split()[0],
        "sources": sources
    }
    return jsonify(response_data)
