from kiteconnect import KiteConnect

# Replace with your actual API Key and Secret
api_key = "3j4h5xt32kyqcol2"
api_secret = "7tojgmld34kablureumsvmnjln9dsh16"

# Initialize KiteConnect
kite = KiteConnect(api_key=api_key)

# Generate login URL
print("=" * 50)
print("STEP 1: Copy this URL and open in your browser:")
print("=" * 50)
print(kite.login_url())
print("=" * 50)
print("\nAfter login, you'll be redirected to a URL like:")
print("http://127.0.0.1:5000/?request_token=XXXXX&action=login&status=success")
print("\nCopy the 'request_token' value (the XXXXX part)")
