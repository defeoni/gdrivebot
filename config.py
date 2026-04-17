"""
Configuration management untuk GDrive Bot
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables dari .env file
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    # Jika .env tidak ada, cari .env.example
    env_example = Path(__file__).parent / '.env.example'
    if env_example.exists():
        print(f"⚠️  File .env tidak ditemukan. Salin dari .env.example dan sesuaikan konfigurasi.")

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8338375836:AAFZzH66ZsThZP-z7dwlgF1t_xlYQAQpJPQ')
CLAUDE_API = os.getenv('CLAUDE_API', '')

# Google Drive Configuration
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.pickle')
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Finance Data
FINANCE_FILE = 'finance_data.json'

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'bot.log')

# Proxy Configuration (optional)
PROXY_URL = os.getenv('PROXY_URL', '')
PROXY_USERNAME = os.getenv('PROXY_USERNAME', '')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD', '')

def validate_config():
    """Validasi konfigurasi yang diperlukan"""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN tidak dikonfigurasi")
    if not CLAUDE_API:
        print("⚠️  Warning: CLAUDE_API tidak dikonfigurasi")
    if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        print(f"⚠️  Warning: {GOOGLE_CREDENTIALS_FILE} tidak ditemukan")
    return True
