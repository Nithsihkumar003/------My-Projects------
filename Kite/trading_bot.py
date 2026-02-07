from kiteconnect import KiteConnect
import json

# Your API credentials
api_key = "3j4h5xt32kyqcol2"  # Replace with your actual API key


# Load saved token
def load_token():
    with open('access_token.json', 'r') as f:
        return json.load(f)

# Initialize Kite
token_data = load_token()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token_data['access_token'])

print(f"✅ Connected as User: {token_data['user_id']}")
print("=" * 50)

# Get your profile
profile = kite.profile()
print(f"Name: {profile['user_name']}")
print(f"Email: {profile['email']}")
print("=" * 50)

# Get your holdings
print("\n📊 YOUR HOLDINGS:")
print("=" * 50)
holdings = kite.holdings()
if holdings:
    for h in holdings:
        print(f"Stock: {h['tradingsymbol']}")
        print(f"  Quantity: {h['quantity']}")
        print(f"  Avg Price: ₹{h['average_price']}")
        print(f"  Current Value: ₹{h['last_price'] * h['quantity']}")
        pnl = (h['last_price'] - h['average_price']) * h['quantity']
        print(f"  P&L: ₹{pnl:.2f}")
        print("-" * 30)
else:
    print("No holdings found")

# Get today's positions
print("\n📈 TODAY'S POSITIONS:")
print("=" * 50)
positions = kite.positions()
net_positions = positions['net']
if net_positions:
    for p in net_positions:
        if p['quantity'] != 0:
            print(f"Stock: {p['tradingsymbol']}")
            print(f"  Quantity: {p['quantity']}")
            print(f"  P&L: ₹{p['pnl']:.2f}")
            print("-" * 30)
else:
    print("No positions today")

# Get account margins
print("\n💰 ACCOUNT BALANCE:")
print("=" * 50)
margins = kite.margins()
equity = margins['equity']
print(f"Available Cash: ₹{equity['available']['live_balance']:.2f}")
print(f"Used Margin: ₹{equity['utilised']['debits']:.2f}")
print("=" * 50)
