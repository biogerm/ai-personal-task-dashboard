import os
import sys
import time
import subprocess
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger("cast.screen")

def is_rest_time(config):
    hour = datetime.now().hour
    start_hour = config.get("cast", {}).get("restStartHour", 1)
    end_hour = config.get("cast", {}).get("restEndHour", 6)
    
    if end_hour > start_hour:
        # e.g. rest from 1 to 6. Rest is >= 1 and < 6
        return hour >= start_hour and hour < end_hour
    else:
        # e.g. rest from 23 to 6. Rest is >= 23 or < 6
        return hour >= start_hour or hour < end_hour

def start_screen_cast(config):
    try:
        time.sleep(5)
        
        if is_rest_time(config):
            logger.info("Currently night time, skipping cast startup.")
            return
            
        port = config.get("server", {}).get("port", 3000)
        host = config.get("server", {}).get("host", "127.0.0.1")
        if host in ["0.0.0.0", "127.0.0.1", "localhost"]:
            import socket
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    host = s.getsockname()[0]
            except Exception:
                pass
                
        dashboard_url = f"http://{host}:{port}"
        nest_hub_name = config.get("cast", {}).get("nestHubName")

        if not nest_hub_name:
            logger.warning("nestHubName not specified in config")
            return
            
        logger.info("Preparing to cast to %s using catt", nest_hub_name)
        
        # Stop existing session first to ensure a hard reload
        stop_cmd = "timeout 15 {} -m catt.cli -d '{}' stop".format(sys.executable, nest_hub_name)
        subprocess.run(stop_cmd, shell=True, errors='ignore')
        time.sleep(3)
        
        cmd = "timeout 20 {} -m catt.cli -d '{}' cast_site {}".format(sys.executable, nest_hub_name, dashboard_url)
        
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True, errors='ignore')
        
        if process.returncode == 0:
            logger.info("Cast command executed successfully. Output: %s", process.stdout.strip())
        else:
            logger.warning("Cast command failed with code: %s. Error: %s", process.returncode, process.stderr.strip())
            
    except Exception as e:
        logger.warning("Cast operation failed: %s", str(e))

def check_screen_cast(config):
    nest_hub_name = config.get("cast", {}).get("nestHubName")
    if not nest_hub_name:
        return

    try:
        cmd = "timeout 15 {} -m catt.cli -d '{}' info".format(sys.executable, nest_hub_name)
        # Using subprocess to capture output
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        output = out.decode('utf-8', errors='ignore')
        
        # Check output for running apps
        is_dashcast = "DashCast" in output
        # Only consider it idle if it is explicitly the Backdrop/Ambient screen.
        # Do not use "Default Media Receiver" as it might be used for background music.
        is_backdrop = (
            "display_name: Backdrop" in output or 
            "display_name: Ambient" in output or 
            "display_name: None" in output
        )
        
        # If DashCast is technically the active app but the device is in standby (screen off/sleeping),
        # we need to recast it to wake the screen back up.
        if is_dashcast and "is_stand_by: True" in output:
            is_dashcast = False
            is_backdrop = True
        
        # Handle night time logic
        if is_rest_time(config):
            if is_dashcast:
                logger.info("Night time detected, preparing to stop cast to let Hub rest...")
                stop_cmd = "timeout 15 {} -m catt.cli -d '{}' stop".format(sys.executable, nest_hub_name)
                subprocess.run(stop_cmd, shell=True)
            else:
                logger.info("Night time, Hub is not casting.")
            return

        # Only recast if screen is not running DashCast and is idle/Backdrop.
        # This avoids interrupting YouTube or Spotify.
        if not is_dashcast and is_backdrop:
            logger.info("Hub is in standby, preparing to recast Dashboard...")
            start_screen_cast(config)
        elif not is_dashcast:
            logger.info("Hub is running another app, will not hijack screen.")
    except Exception as e:
        logger.error("Failed to check cast status: %s", str(e))
