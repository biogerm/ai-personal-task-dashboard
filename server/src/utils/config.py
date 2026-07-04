import os
import json
import logging
from dotenv import load_dotenv

def load_config():
    # Load .env
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    env_path = os.path.join(base_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        logging.warning(".env file not found, reading from environment variables.")

    # Load config.json
    config_path = os.path.join(base_dir, 'config.json')
    if not os.path.exists(config_path):
        raise FileNotFoundError("config.json not found")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Inject credentials
    config['credentials'] = {
        'ICLOUD_USERNAME': os.environ.get('ICLOUD_USERNAME'),
        'ICLOUD_APP_PASSWORD': os.environ.get('ICLOUD_APP_PASSWORD'),
        'NOTION_API_TOKEN': os.environ.get('NOTION_API_TOKEN'),
        'NOTION_DATABASE_ID': os.environ.get('NOTION_DATABASE_ID'),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY')
    }

    # Validate
    missing = [k for k, v in config['credentials'].items() if not v]
    if missing:
        raise ValueError("Missing required credentials: {}".format(", ".join(missing)))

    return config
