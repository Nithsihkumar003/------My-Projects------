from flask import Flask, request, redirect
from kite_tools import KiteTools
from config import KiteConfig
import threading
import webbrowser
import time
import json

app = Flask(__name__)
kite_tools = KiteTools()

# Store the request token when callback is received
callback_received = False
callback_error = None


@app.route('/callback')
def callback_handler():
    """Handle OAuth callback from Kite"""
    global callback_received, callback_error

    request_token = request.args.get('request_token')
    status = request.args.get('status')

    if status == 'success' and request_token:
        # Store request token
        KiteConfig.set_request_token(request_token)

        # Generate session
        result = kite_tools.generate_session(request_token)

        if result.get('success'):
            callback_received = True
            return """
            <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: green;">✅ Login Successful!</h1>
                    <p>You can close this window now.</p>
                    <p>Access Token: {}</p>
                </body>
            </html>
            """.format(result['access_token'][:20] + "...")
        else:
            callback_error = result.get('error', 'Unknown error')
            return f"""
            <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: red;">❌ Login Failed</h1>
                    <p>Error: {callback_error}</p>
                </body>
            </html>
            """
    else:
        callback_error = "Login was cancelled or failed"
        return """
        <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: red;">❌ Login Cancelled</h1>
                <p>You can close this window.</p>
            </body>
        </html>
        """


def start_flask_server():
    """Start Flask server in background"""
    app.run(port=KiteConfig.CALLBACK_PORT, debug=False, use_reloader=False)


class KiteMCPServer:
    """MCP Server for Kite Connect with AI Agent capabilities"""

    def __init__(self):
        self.kite_tools = KiteTools()
        self.flask_thread = None

    def start_server(self):
        """Start the Flask callback server"""
        if not self.flask_thread or not self.flask_thread.is_alive():
            self.flask_thread = threading.Thread(target=start_flask_server, daemon=True)
            self.flask_thread.start()
            time.sleep(1)  # Give server time to start
            print(f"✅ Callback server started on port {KiteConfig.CALLBACK_PORT}")

    def login(self):
        """
        Initiate Kite login process
        Returns the login URL and starts callback server
        """
        global callback_received, callback_error
        callback_received = False
        callback_error = None

        # Start callback server
        self.start_server()

        # Get login URL
        login_url = self.kite_tools.get_login_url()

        print("\n" + "=" * 60)
        print("🔐 KITE LOGIN PROCESS")
        print("=" * 60)
        print(f"\n📌 Step 1: Opening browser for login...")
        print(f"🌐 Login URL: {login_url}\n")

        # Open browser automatically
        webbrowser.open(login_url)

        print("⏳ Waiting for you to complete login in browser...")
        print("   (Login with your Zerodha credentials)")
        print("   (Complete OTP verification)")
        print("   (Click 'Authorize' when prompted)\n")

        # Wait for callback (max 2 minutes)
        timeout = 120
        start_time = time.time()

        while not callback_received and not callback_error:
            if time.time() - start_time > timeout:
                return {
                    "success": False,
                    "error": "Login timeout. Please try again."
                }
            time.sleep(1)

        if callback_received:
            print("✅ Login successful! Access token received.\n")
            return {
                "success": True,
                "message": "✅ Successfully logged in!",
                "access_token": KiteConfig.ACCESS_TOKEN
            }
        else:
            return {
                "success": False,
                "error": callback_error
            }

    def process_command(self, command):
        """
        Process natural language commands from AI agent

        Examples:
        - "get my profile"
        - "show my holdings"
        - "get positions"
        - "buy 1 share of INFY at market price"
        - "sell 10 shares of RELIANCE"
        """
        command_lower = command.lower()

        # Profile
        if 'profile' in command_lower:
            return self.kite_tools.get_profile()

        # Holdings
        elif 'holding' in command_lower:
            return self.kite_tools.get_holdings()

        # Positions
        elif 'position' in command_lower:
            return self.kite_tools.get_positions()

        # Margins
        elif 'margin' in command_lower or 'balance' in command_lower:
            return self.kite_tools.get_margins()

        # Buy order
        elif 'buy' in command_lower:
            return self._parse_order_command(command, 'BUY')

        # Sell order
        elif 'sell' in command_lower:
            return self._parse_order_command(command, 'SELL')

        # Quote
        elif 'quote' in command_lower or 'price' in command_lower:
            return self._parse_quote_command(command)

        # Logout
        elif 'logout' in command_lower or 'invalidate' in command_lower:
            return self.kite_tools.invalidate_session()

        else:
            return {
                "success": False,
                "error": "Command not recognized. Try: 'get profile', 'show holdings', 'buy 1 INFY', etc."
            }

    def _parse_order_command(self, command, transaction_type):
        """Parse order commands like 'buy 10 INFY' or 'sell 5 RELIANCE at 2800'"""
        try:
            words = command.upper().split()

            # Find quantity
            quantity = None
            symbol = None
            price = None

            for i, word in enumerate(words):
                if word.isdigit():
                    quantity = int(word)
                    # Next word might be symbol
                    if i + 1 < len(words):
                        symbol = words[i + 1]
                elif 'AT' in word and i + 1 < len(words):
                    price = float(words[i + 1])

            if not quantity or not symbol:
                return {
                    "success": False,
                    "error": "Could not parse order. Use format: 'buy 10 INFY' or 'sell 5 RELIANCE at 2800'"
                }

            order_type = 'LIMIT' if price else 'MARKET'

            return self.kite_tools.place_order(
                symbol=symbol,
                exchange='NSE',
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=order_type,
                product='CNC',
                price=price
            )
        except Exception as e:
            return {"success": False, "error": f"Error parsing command: {str(e)}"}

    def _parse_quote_command(self, command):
        """Parse quote commands like 'get price of INFY'"""
        try:
            words = command.upper().split()
            symbols = [w for w in words if len(w) > 2 and w.isalpha() and w not in ['GET', 'PRICE', 'QUOTE', 'OF']]

            if not symbols:
                return {"success": False, "error": "No stock symbol found"}

            instruments = [f"NSE:{s}" for s in symbols]
            return self.kite_tools.get_quote(instruments)
        except Exception as e:
            return {"success": False, "error": str(e)}


# Main execution
if __name__ == "__main__":
    print("\n🤖 Kite MCP AI Trading Server")
    print("=" * 60)

    # Initialize server
    server = KiteMCPServer()

    # Login
    print("\n🔐 Starting login process...")
    login_result = server.login()

    if not login_result.get('success'):
        print(f"❌ Login failed: {login_result.get('error')}")
        exit(1)

    print("\n✅ Ready to accept commands!")
    print("=" * 60)

    # Interactive command loop
    print("\n💡 Examples:")
    print("  - get my profile")
    print("  - show my holdings")
    print("  - get positions")
    print("  - buy 1 INFY")
    print("  - sell 5 RELIANCE")
    print("  - get price of INFY")
    print("  - logout")
    print("\nType 'exit' to quit\n")

    while True:
        try:
            command = input("🤖 Command: ").strip()

            if command.lower() in ['exit', 'quit']:
                print("\n👋 Goodbye!")
                break

            if not command:
                continue

            # Process command
            result = server.process_command(command)

            # Display result
            print("\n" + "=" * 60)
            print(json.dumps(result, indent=2))
            print("=" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")

