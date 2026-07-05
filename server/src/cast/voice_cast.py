import os
import time
from src.utils.logger import get_logger

logger = get_logger("cast.voice")


def _generate_audio(text, output_path):
    try:
        from gtts import gTTS
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tts = gTTS(text=text, lang='zh-CN')
        tts.save(output_path)
        return True
    except Exception as e:
        logger.warning("TTS Generation Error: %s", str(e))
        return False


def cast_voice_summary(text, device_name=None, config=None):
    try:
        import pychromecast

        port = 3000
        if config and "server" in config and "port" in config["server"]:
            port = config["server"]["port"]

        cwd = os.getcwd()
        output_path = os.path.join(cwd, "static", "audio", "summary.mp3")

        if not _generate_audio(text, output_path):
            return

        host = config.get("server", {}).get("host", "127.0.0.1") if config else "127.0.0.1"
        if host in ["0.0.0.0", "127.0.0.1", "localhost"]:
            import socket
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    host = s.getsockname()[0]
            except Exception:
                pass
                
        url_fmt = f"http://{host}:{port}/static/audio/summary.mp3"
        mp3_url = url_fmt

        res = pychromecast.get_chromecasts(timeout=10)
        if isinstance(res, tuple) and len(res) == 2:
            chromecasts, browser = res
        else:
            chromecasts = res
            browser = None

        found_device = None
        device_names = []
        for cc in chromecasts:
            device_names.append(cc.device.friendly_name)
            if device_name:
                if cc.device.friendly_name == device_name:
                    found_device = cc
            else:
                cast_type = getattr(
                    cc, 'cast_type', getattr(cc.device, 'cast_type', None)
                )
                if cast_type == 'audio':
                    found_device = cc
                    break

        if not found_device and not device_name and chromecasts:
            found_device = chromecasts[0]

        if not found_device:
            names_str = ", ".join(device_names)
            logger.warning("Target voice device not found. Discovered: %s", names_str)
            if browser:
                pychromecast.discovery.stop_discovery(browser)
            if os.path.exists(output_path):
                os.remove(output_path)
            return

        try:
            device = found_device
            device.wait()
            mc = device.media_controller
            mc.play_media(mp3_url, 'audio/mp3')
            mc.block_until_active()
            logger.info("Started playing voice summary on %s", device.device.friendly_name)

            while True:
                time.sleep(2)
                mc.update_status()
                if mc.status.player_state not in ['PLAYING', 'BUFFERING']:
                    break
        except Exception as inner_e:
            logger.warning("Voice playback error: %s", str(inner_e))
        finally:
            if browser:
                pychromecast.discovery.stop_discovery(browser)
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass

    except Exception as e:
        logger.warning("Voice broadcast error: %s", str(e))
