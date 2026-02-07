from kiteconnect import KiteConnect
import json
from datetime import datetime

# Save token
def save_token(access_token, user_id):
    token_data = {
        'access_token': access_token,
        'user_id': user_id,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    with open('access_token.json', 'w') as f:
        json.dump(token_data, f)
    print("✅ Token saved successfully!")

# Load token
def load_token():
    try:
        with open('access_token.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# Save your current token
save_token('ceCqLpeBEZYjiTYTAHdqvVT1VTJTrS1I', 'ZK4021')
