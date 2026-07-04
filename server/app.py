import os
import sys
import threading
import logging
from flask import send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import load_config
from src.utils.logger import get_logger
from src.merger import TaskMerger
from src.app import create_app
from src.cast.screen_cast import start_screen_cast, check_screen_cast

logger = get_logger("app")

def run():
    # 1. Load config
    try:
        config = load_config()
    except Exception as e:
        logger.error("Failed to load config: %s", e)
        sys.exit(1)

    # 2. Init TaskMerger
    merger = TaskMerger(config)
    
    # 3. Create Flask app and attach merger
    app = create_app()
    app.merger = merger

    # 4. Add static routing for index.html at root
    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    # 5. First data sync
    logger.info("Performing initial data sync...")
    merger.refresh()

    # 6. Setup APScheduler
    scheduler = BackgroundScheduler()
    interval_mins = config.get("sync", {}).get("intervalMinutes", 5)
    scheduler.add_job(merger.refresh, 'interval', minutes=interval_mins)
    
    # Setup Screen Cast checking job
    if config.get("cast", {}).get("autoScreenCast", True):
        scheduler.add_job(check_screen_cast, 'interval', minutes=10, args=[config])

    scheduler.start()

    # 7. Start Cast in background
    if config.get("cast", {}).get("autoScreenCast", True):
        def _cast():
            start_screen_cast(config)
        threading.Thread(target=_cast, daemon=True).start()

    # 8. Run server
    host = config.get("server", {}).get("host", "0.0.0.0")
    port = config.get("server", {}).get("port", 3000)
    logger.info("Starting Personal Dashboard on %s:%s", host, port)
    
    # Use threaded=True for better concurrency if not using WSGI server
    app.run(host=host, port=port, threaded=True, use_reloader=False)

if __name__ == "__main__":
    run()
