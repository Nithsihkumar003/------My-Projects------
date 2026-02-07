from kiteconnect import KiteConnect
import json
import time
from datetime import datetime
import yfinance as yf


# Load saved token
def load_token():
    with open('access_token.json', 'r') as f:
        return json.load(f)


# Initialize Kite
token_data = load_token()
api_key = "3j4h5xt32kyqcol2"  # Your API key
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token_data['access_token'])

print("✅ Yahoo Finance Bot Started Successfully!")
print(f"💼 Trading Account: {token_data['user_id']}")
print("=" * 60)

# ========== UPDATED ALERTS FOR ALL YOUR STOCKS ==========

ALERTS = [
    # === STOP LOSS - Limit Heavy Losses ===
    {
        "symbol": "FCONSUMER.BO",  # BSE stock, use .BO
        "nse_symbol": "FCONSUMER-Z",
        "target_price": 0.30,  # Currently 0.37, avg 4.31 - STOP LOSS
        "action": "SELL",
        "quantity": 700,
        "condition": "below",
        "triggered": False
    },
    {
        "symbol": "NAVKETAN9.BO",
        "nse_symbol": "NAVKETAN9-Z",
        "target_price": 0.90,  # Currently 1.04, avg 2.55 - STOP LOSS
        "action": "SELL",
        "quantity": 1000,
        "condition": "below",
        "triggered": False
    },
    {
        "symbol": "ALSTONE.NS",
        "nse_symbol": "ALSTONE",
        "target_price": 0.15,  # Currently 0.19, avg 1.07 - STOP LOSS
        "action": "SELL",
        "quantity": 500,
        "condition": "below",
        "triggered": False
    },
    {
        "symbol": "GUJTLRM.NS",
        "nse_symbol": "GUJTLRM",
        "target_price": 0.50,  # Currently 0.61, avg 1.51 - STOP LOSS
        "action": "SELL",
        "quantity": 950,
        "condition": "below",
        "triggered": False
    },

    # === RECOVERY TARGETS - Sell at Breakeven ===
    {
        "symbol": "KUSHAL.BO",
        "nse_symbol": "KUSHAL-Z",
        "target_price": 3.40,  # Your avg price - breakeven exit
        "action": "SELL",
        "quantity": 445,
        "condition": "above",
        "triggered": False
    },
    {
        "symbol": "AONETOTAL.NS",
        "nse_symbol": "AONETOTAL",
        "target_price": 11.71,  # Your avg price - breakeven
        "action": "SELL",
        "quantity": 55,  # Sell half
        "condition": "above",
        "triggered": False
    },

    # === ETF PROFIT BOOKING ===
    {
        "symbol": "MID150CASE.NS",
        "nse_symbol": "MID150CASE",
        "target_price": 10.78,  # Your avg price - breakeven
        "action": "SELL",
        "quantity": 50,  # Sell half
        "condition": "above",
        "triggered": False
    },
    {
        "symbol": "MIDCAPETF.NS",
        "nse_symbol": "MIDCAPETF",
        "target_price": 21.98,  # Your avg price - breakeven
        "action": "SELL",
        "quantity": 30,  # Sell half
        "condition": "above",
        "triggered": False
    },
    {
        "symbol": "SML100CASE.NS",
        "nse_symbol": "SML100CASE",
        "target_price": 9.66,  # Your avg price - breakeven
        "action": "SELL",
        "quantity": 35,  # Sell half
        "condition": "above",
        "triggered": False
    },
    {
        "symbol": "TOP100CASE.NS",
        "nse_symbol": "TOP100CASE",
        "target_price": 10.83,  # Your avg price - breakeven
        "action": "SELL",
        "quantity": 35,  # Sell half
        "condition": "above",
        "triggered": False
    },

    # === AVERAGING DOWN - Buy More on Dips ===
    {
        "symbol": "MID150CASE.NS",
        "nse_symbol": "MID150CASE",
        "target_price": 10.20,  # Buy if dips below current
        "action": "BUY",
        "quantity": 10,
        "condition": "below",
        "triggered": False
    },
    {
        "symbol": "MIDCAPETF.NS",
        "nse_symbol": "MIDCAPETF",
        "target_price": 20.50,  # Buy if dips below current
        "action": "BUY",
        "quantity": 10,
        "condition": "below",
        "triggered": False
    },

    # === MUTUAL FUND PROFIT PROTECTION ===
    {
        "symbol": "0P00018R53.BO",  # MIRAE ASSET ELSS
        "nse_symbol": "MIRAE ASSET ELSS",
        "target_price": 53.00,  # Book profits if drops from 56.12
        "action": "SELL",
        "quantity": 100000,  # Partial exit
        "condition": "below",
        "triggered": False
    }
]


# ========== BOT FUNCTIONS ==========

def get_live_price(symbol):
    """Get current price from Yahoo Finance - COMPLETELY FREE"""
    try:
        ticker = yf.Ticker(symbol)

        # Try intraday data first
        hist = ticker.history(period='1d', interval='5m')

        if not hist.empty:
            price = hist['Close'].iloc[-1]
            return round(price, 2)

        # Fallback to daily
        hist = ticker.history(period='5d')
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            return round(price, 2)

        return None

    except Exception as e:
        return None


def place_order(nse_symbol, action, quantity):
    """SIMULATION MODE - No real orders"""
    print(f"   🔔 SIMULATION: {action} {quantity} shares of {nse_symbol}")
    print(f"   💡 Real trading disabled for safety")
    return "SIMULATED"


def check_alerts():
    """Check all price alerts"""
    print(f"\n⏰ {datetime.now().strftime('%d-%b %H:%M:%S')}")
    print("-" * 60)

    for alert in ALERTS:
        if alert['triggered']:
            continue

        symbol = alert['symbol']
        nse_symbol = alert['nse_symbol']

        current_price = get_live_price(symbol)

        if current_price is None:
            print(f"⚠️  {nse_symbol}: Unable to fetch price")
            continue

        target = alert['target_price']
        condition = alert['condition']
        action = alert['action']

        status = "📉" if condition == "below" else "📈"
        diff = current_price - target
        diff_pct = (diff / target) * 100

        print(f"{status} {nse_symbol}: ₹{current_price:.2f} → Target: ₹{target:.2f} | Diff: {diff_pct:+.1f}%")

        # Check trigger
        triggered = False
        if condition == "below" and current_price <= target:
            triggered = True
        elif condition == "above" and current_price >= target:
            triggered = True

        if triggered:
            print(f"   🚨 ALERT! {nse_symbol} hit ₹{current_price:.2f}")
            order_id = place_order(nse_symbol, action, alert['quantity'])
            if order_id:
                alert['triggered'] = True


# ========== MAIN LOOP ==========

print("\n🤖 Enhanced Price Alert Bot v2.0")
print("📊 Yahoo Finance FREE data | All 13 alerts active")
print(f"📌 Monitoring: {len(ALERTS)} price targets")
print("⚠️  SIMULATION MODE: Safe testing, no real orders")
print("Press Ctrl+C to stop\n")
print("=" * 60)

try:
    check_count = 0
    while True:
        check_alerts()
        check_count += 1

        if all(alert['triggered'] for alert in ALERTS):
            print("\n✅ All alerts triggered! Bot stopping.")
            break

        print(f"\n💤 Next check in 60 seconds... (#{check_count})")
        time.sleep(60)

except KeyboardInterrupt:
    print(f"\n\n⛔ Bot stopped by user | Total checks: {check_count}")
    print("=" * 60)
