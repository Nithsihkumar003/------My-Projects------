from kiteconnect import KiteConnect
import json
import time
from datetime import datetime

# Load saved token
def load_token():
    with open('access_token.json', 'r') as f:
        return json.load(f)

# Initialize Kite
token_data = load_token()
api_key = "3j4h5xt32kyqcol2"  # Your actual API key
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token_data['access_token'])

print("✅ Bot Started Successfully!")
print(f"💼 Trading Account: {token_data['user_id']}")
print("=" * 60)


# ========== YOUR PERSONALIZED TRADING RULES ==========

ALERTS = [
    # Stop Loss
    {
        "symbol": "NSE:ALSTONE",
        "target_price": 0.15,
        "action": "SELL",
        "quantity": 500,
        "condition": "below",
        "triggered": False
    },
    {
        "symbol": "NSE:GUJTLRM",
        "target_price": 0.50,
        "action": "SELL",
        "quantity": 950,
        "condition": "below",
        "triggered": False
    },

    # Profit Booking
    {
        "symbol": "NSE:AONETOTAL",
        "target_price": 12.00,
        "action": "SELL",
        "quantity": 44,
        "condition": "above",
        "triggered": False
    },
    {
        "symbol": "NSE:MIDCAPETF",
        "target_price": 22.50,
        "action": "SELL",
        "quantity": 24,
        "condition": "above",
        "triggered": False
    },

    # Averaging Down
    {
        "symbol": "NSE:MID150CASE",
        "target_price": 10.50,
        "action": "BUY",
        "quantity": 10,
        "condition": "below",
        "triggered": False
    },
    {
        "symbol": "NSE:SML100CASE",
        "target_price": 9.20,
        "action": "BUY",
        "quantity": 10,
        "condition": "below",
        "triggered": False
    },

    # Breakeven Exit
    {
        "symbol": "NSE:TOP100CASE",
        "target_price": 10.84,
        "action": "SELL",
        "quantity": 28,
        "condition": "above",
        "triggered": False
    }
]


# ========== BOT FUNCTIONS ==========

def get_live_price(symbol):
    """Get current market price"""
    try:
        quote = kite.quote(symbol)
        return quote[symbol]['last_price']
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None


def place_order(symbol, action, quantity):
    """Place market order"""
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NSE,
            tradingsymbol=symbol.split(':')[1],
            transaction_type=kite.TRANSACTION_TYPE_BUY if action == "BUY" else kite.TRANSACTION_TYPE_SELL,
            quantity=quantity,
            product=kite.PRODUCT_CNC,
            order_type=kite.ORDER_TYPE_MARKET
        )
        print(f"   ✅ ORDER PLACED! ID: {order_id}")
        return order_id
    except Exception as e:
        print(f"   ❌ Order failed: {e}")
        return None


def check_alerts():
    """Check all price alerts"""
    print(f"\n⏰ {datetime.now().strftime('%d-%b %H:%M:%S')}")
    print("-" * 60)

    for alert in ALERTS:
        if alert['triggered']:
            continue

        symbol = alert['symbol']
        current_price = get_live_price(symbol)

        if current_price is None:
            continue

        target = alert['target_price']
        condition = alert['condition']
        action = alert['action']

        # Show status
        status = "📉" if condition == "below" else "📈"
        print(f"{status} {symbol}: ₹{current_price:.2f} → Target: ₹{target} ({condition})")

        # Check trigger
        triggered = False
        if condition == "below" and current_price <= target:
            triggered = True
        elif condition == "above" and current_price >= target:
            triggered = True

        if triggered:
            print(f"   🚨 ALERT! Executing {action} {alert['quantity']} shares...")
            order_id = place_order(symbol, action, alert['quantity'])
            if order_id:
                alert['triggered'] = True


# ========== MAIN LOOP ==========

print("\n🤖 Price Alert Bot Running...")
print("Monitoring:", len(ALERTS), "alerts")
print("Press Ctrl+C to stop\n")
print("=" * 60)

try:
    while True:
        check_alerts()

        if all(alert['triggered'] for alert in ALERTS):
            print("\n✅ All alerts triggered! Stopping bot.")
            break

        time.sleep(30)  # Check every 30 seconds

except KeyboardInterrupt:
    print("\n⛔ Bot stopped by user")
