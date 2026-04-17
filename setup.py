"""
Setup dan start GDrive Bot dengan konfigurasi dari environment
"""
import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_bot():
    """Setup bot dengan konfigurasi"""
    try:
        # Import config
        from config import validate_config, BOT_TOKEN, CLAUDE_API
        
        # Validasi konfigurasi
        validate_config()
        
        logger.info("✅ Konfigurasi valid")
        logger.info(f"Bot Token: {BOT_TOKEN[:20]}...")
        logger.info(f"Claude API: {'Configured' if CLAUDE_API else 'Not configured'}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Setup gagal: {e}")
        return False

def main():
    """Main entry point"""
    if not setup_bot():
        sys.exit(1)
    
    logger.info("Bot siap dijalankan!")
    logger.info("Untuk menjalankan bot, gunakan: python -m gdrivebot")

if __name__ == '__main__':
    main()
