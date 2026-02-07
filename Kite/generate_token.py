from kiteconnect import KiteConnect
import json
from datetime import datetime

# Your credentials
api_key = "3j4h5xt32kyqcol2"
api_secret = "7tojgmld34kablureumsvmnjln9dsh16"

# Initialize
kite = KiteConnect(api_key=api_key)

# Step 1: Generate login URL
print("STEP 1: Copy this URL and open in your browser:")
print("=" * 60)
print(kite.login_url())
print("=" * 60)

print("\nAfter login, you'll be redirected to a URL like:")
print("http://127.0.0.1:5000/?request_token=XXXXX&action=login&status=success")
print("\nCopy the 'request_token' value (the XXXXX part)")

request_token = input("\nPaste request_token here: ").strip()

try:
    # Generate session
    data = kite.generate_session(request_token, api_secret=api_secret)

    print("\n" + "=" * 50)
    print("✅ Authentication Successful!")
    print("=" * 50)
    print(f"Access Token: {data['access_token']}")
    print(f"User ID: {data['user_id']}")
    print("=" * 50)

    # Auto-save token
    token_data = {
        'access_token': data['access_token'],
        'user_id': data['user_id'],
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    with open('access_token.json', 'w') as f:
        json.dump(token_data, f, indent=2)

    print("\n✅ Token automatically saved to access_token.json")
    print("⚠️ Valid for 24 hours (until 6 AM tomorrow)")

except Exception as e:
    print(f"\n❌ Error: {e}")
