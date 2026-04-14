"""
Configuratie voor De Trouwvideograaf Blog Generator.
Laad instellingen vanuit .env bestand of environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Laad .env bestand (als het bestaat)
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# ─── CLAUDE API ───────────────────────────────────────────────────────────────
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-haiku-4-5-20251001')  # Goedkoopste model

# ─── BLOG INSTELLINGEN ────────────────────────────────────────────────────────
BLOG_DIR = os.getenv('BLOG_DIR', str(Path(__file__).parent.parent))
GITHUB_REPO = os.getenv('GITHUB_REPO', 'https://github.com/johnquote/detrouwvideograaf-blog.git')
BLOG_BASE_URL = os.getenv('BLOG_BASE_URL', 'https://blog.detrouwvideograaf.net')

# ─── EMAIL INSTELLINGEN ───────────────────────────────────────────────────────
EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
EMAIL_FROM = os.getenv('EMAIL_FROM', '')       # bijv. jouw@gmail.com
EMAIL_TO = os.getenv('EMAIL_TO', '')           # jouw@gmail.com
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')  # Gmail App Password

# ─── VALIDATIE ────────────────────────────────────────────────────────────────
def check_config():
    """Controleer of de verplichte configuratie aanwezig is."""
    errors = []

    if not CLAUDE_API_KEY:
        errors.append("CLAUDE_API_KEY is niet ingesteld")

    if errors:
        print("\nCONFIGURATIE FOUT:")
        for error in errors:
            print(f"  - {error}")
        print(f"\nMaak een .env bestand in: {env_path}")
        print("Gebruik .env.example als voorbeeld.\n")
        return False

    return True
