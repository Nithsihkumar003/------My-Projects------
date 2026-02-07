import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN_CACHE_FILE = 'token_cache.json'

class KiteConfig:
    """Configuration for Kite Connect API"""

    API_KEY = os.getenv('KITE_API_KEY')
    API_SECRET = os.getenv('KITE_API_SECRET')
    USER_ID = os.getenv('KITE_USER_ID')
    PASSWORD = os.getenv('KITE_PASSWORD')
    CALLBACK_PORT = int(os.getenv('CALLBACK_PORT', 3456))
    REDIRECT_URL = f"http://127.0.0.1:{CALLBACK_PORT}/callback"

    # Session storage
    ACCESS_TOKEN = None
    REQUEST_TOKEN = None

    @classmethod
    def set_access_token(cls, token):
        """Store and save access token"""
        cls.ACCESS_TOKEN = token
        cls.save_token()

    @classmethod
    def set_request_token(cls, token):
        """Store request token"""
        cls.REQUEST_TOKEN = token

    @classmethod
    def save_token(cls):
        """Save access token to file"""
        if cls.ACCESS_TOKEN:
            with open(TOKEN_CACHE_FILE, 'w') as f:
                json.dump({'access_token': cls.ACCESS_TOKEN}, f)
            print("💾 Token saved to cache")

    @classmethod
    def load_token(cls):
        """Load access token from file"""
        try:
            if os.path.exists(TOKEN_CACHE_FILE):
                with open(TOKEN_CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    cls.ACCESS_TOKEN = data.get('access_token')
                    if cls.ACCESS_TOKEN:
                        print("✅ Token loaded from cache")
                        return True
        except Exception as e:
            print(f"⚠️ Could not load token: {e}")
        return False

    @classmethod
    def is_authenticated(cls):
        """Check if we have a valid access token"""
        return cls.ACCESS_TOKEN is not None

    @classmethod
    def validate(cls):
        """Validate that all required config is present"""
        if not cls.API_KEY:
            raise ValueError("KITE_API_KEY not found in .env file")
        if not cls.API_SECRET:
            raise ValueError("KITE_API_SECRET not found in .env file")
        if not cls.USER_ID:
            raise ValueError("KITE_USER_ID not found in .env file")
        return True

# Validate config on import
try:
    KiteConfig.validate()
    print("✅ Configuration loaded successfully")
    # Try to load saved token
    KiteConfig.load_token()
except ValueError as e:
    print(f"❌ Configuration error: {e}")
