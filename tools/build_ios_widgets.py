#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, 'server', '.env')
    
    if not os.path.exists(env_path):
        print(f"Error: .env file not found at {env_path}")
        sys.exit(1)
        
    load_dotenv(env_path)
    
    notion_api_key = os.environ.get("NOTION_API_TOKEN")
    notion_db_id = os.environ.get("NOTION_DATABASE_ID")
    
    if not notion_api_key or not notion_db_id:
        print("Error: NOTION_API_TOKEN or NOTION_DATABASE_ID missing in .env")
        sys.exit(1)
        
    dist_dir = os.path.join(root_dir, 'dist', 'ios_widgets')
    os.makedirs(dist_dir, exist_ok=True)
    
    src_dir = os.path.join(root_dir, 'ios_widgets')
    for filename in os.listdir(src_dir):
        if filename.endswith('.js') and not filename.endswith('.test.js'):
            src_file = os.path.join(src_dir, filename)
            dist_file = os.path.join(dist_dir, filename)
            
            with open(src_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Replace placeholders
            content = content.replace('__NOTION_API_KEY__', notion_api_key)
            content = content.replace('__NOTION_DB_ID__', notion_db_id)
            if os.environ.get("NOTION_VIEW_ID"):
                content = content.replace('__NOTION_VIEW_ID__', os.environ.get("NOTION_VIEW_ID"))
            else:
                # If no view ID provided, fallback to default base URL
                content = content.replace('?v=__NOTION_VIEW_ID__', '')
                
            if os.environ.get("OPENAI_API_KEY"):
                content = content.replace('__OPENAI_API_KEY__', os.environ.get("OPENAI_API_KEY"))
            
            app_locale = os.environ.get("APP_LOCALE", "en")
            content = content.replace('__APP_LOCALE__', app_locale)
            
            with open(dist_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"Successfully built {dist_file}")

if __name__ == '__main__':
    main()
