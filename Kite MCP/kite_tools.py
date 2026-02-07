from kiteconnect import KiteConnect
from config import KiteConfig
import json


class KiteTools:
    """Tools for Kite Connect API operations"""

    def __init__(self):
        self._kite = None

    @property
    def kite(self):
        """Get KiteConnect instance with current token"""
        if not self._kite:
            self._kite = KiteConnect(api_key=KiteConfig.API_KEY)

        # Always set the latest access token
        if KiteConfig.ACCESS_TOKEN:
            self._kite.set_access_token(KiteConfig.ACCESS_TOKEN)

        return self._kite

    def get_login_url(self):
        """Get the login URL for OAuth"""
        return self.kite.login_url()

    def generate_session(self, request_token):
        """Generate session using request token"""
        try:
            data = self.kite.generate_session(
                request_token=request_token,
                api_secret=KiteConfig.API_SECRET
            )

            # Store access token
            access_token = data['access_token']
            KiteConfig.set_access_token(access_token)
            self.kite.set_access_token(access_token)

            print(f"✅ Access token set: {access_token[:20]}...")

            return {
                "success": True,
                "access_token": access_token,
                "user_id": data['user_id'],
                "message": "✅ Login successful!"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_profile(self):
        """Get user profile"""
        if not KiteConfig.is_authenticated():
            return {"error": "Not authenticated. Please login first."}

        try:
            # Refresh token before API call
            self.kite.set_access_token(KiteConfig.ACCESS_TOKEN)
            profile = self.kite.profile()
            return {
                "success": True,
                "profile": profile
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_holdings(self):
        """Get user holdings"""
        if not KiteConfig.is_authenticated():
            return {"error": "Not authenticated. Please login first."}

        try:
            self.kite.set_access_token(KiteConfig.ACCESS_TOKEN)
            holdings = self.kite.holdings()
            return {
                "success": True,
                "holdings": holdings
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_positions(self):
        """Get current positions"""
        if not KiteConfig.is_authenticated():
            return {"error": "Not authenticated. Please login first."}

        try:
            self.kite.set_access_token(KiteConfig.ACCESS_TOKEN)
            positions = self.kite.positions()
            return {
                "success": True,
                "positions": positions
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_margins(self, segment='equity'):
        """Get account margins"""
        if not KiteConfig.is_authenticated():
            return {"error": "Not authenticated. Please login first."}

        try:
            self.kite.set_access_token(KiteConfig.ACCESS_TOKEN)
            margins = self.kite.margins(segment)
            return {
                "success": True,
                "margins": margins
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def place_order(self, symbol, exchange, transaction_type, quantity,
                    order_type='MARKET', product='CNC', price=None):
        """Place an order"""
        if not KiteConfig.is_authenticated():
            return {"error": "Not authenticated. Please login first."}

        try:
            self.kite.set_access_token(KiteConfig.ACCESS_TOKEN)

            order_params = {
                'variety': self.kite.VARIETY_REGULAR,
                'exchange': exchange,
                'tradingsymbol': symbol,
                'transaction_type': transaction_type,
                'quantity': quantity,
                'product': product,
                'order_type': order_type
            }

            if order_type == 'LIMIT' and price:
                order_params['price'] = price

            order_id = self.kite.place_order(**order_params)

            return {
                "success": True,
                "order_id": order_id,
                "message": f"✅ Order placed! ID: {order_id}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_quote(self, instruments):
        """Get live quotes"""
        if not KiteConfig.is_authenticated():
            return {"error": "Not authenticated. Please login first."}

        try:
            self.kite.set_access_token(KiteConfig.ACCESS_TOKEN)
            quotes = self.kite.quote(instruments)
            return {
                "success": True,
                "quotes": quotes
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def invalidate_session(self):
        """Logout"""
        if not KiteConfig.is_authenticated():
            return {"error": "Not logged in"}

        try:
            self.kite.invalidate_access_token(KiteConfig.ACCESS_TOKEN)
            KiteConfig.set_access_token(None)
            return {
                "success": True,
                "message": "✅ Logged out"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
