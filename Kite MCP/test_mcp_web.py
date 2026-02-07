from flask import Flask, render_template_string, request, jsonify
from kite_tools import KiteTools
from config import KiteConfig
import json

app = Flask(__name__)
kite_tools = KiteTools()

# HTML Template for Testing Interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kite MCP Inspector</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background: #1e1e1e;
            color: #fff;
        }
        .container {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        h1 { color: #4CAF50; }
        h2 { color: #2196F3; }
        .tool-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .tool {
            background: #383838;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover { background: #45a049; }
        .input-field {
            width: 100%;
            padding: 8px;
            margin: 5px 0;
            background: #2d2d2d;
            border: 1px solid #555;
            color: #fff;
            border-radius: 3px;
        }
        #result {
            background: #1e1e1e;
            padding: 15px;
            border-radius: 5px;
            white-space: pre-wrap;
            font-family: monospace;
            border: 1px solid #555;
            max-height: 400px;
            overflow-y: auto;
        }
        .auth-status {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .auth-yes { background: #1b5e20; }
        .auth-no { background: #b71c1c; }
    </style>
</head>
<body>
    <h1>🤖 Kite MCP Inspector</h1>

    <div class="auth-status {{ 'auth-yes' if authenticated else 'auth-no' }}">
        {% if authenticated %}
            ✅ Authenticated - Ready to trade!
        {% else %}
            ❌ Not authenticated - Login required!
        {% endif %}
    </div>

    <div class="container">
        <h2>📊 Available Tools</h2>
        <div class="tool-grid">

            <div class="tool">
                <h3>👤 Get Profile</h3>
                <p>Get user profile information</p>
                <button onclick="callTool('profile')">Run Tool</button>
            </div>

            <div class="tool">
                <h3>💼 Get Holdings</h3>
                <p>View all your stock holdings</p>
                <button onclick="callTool('holdings')">Run Tool</button>
            </div>

            <div class="tool">
                <h3>📈 Get Positions</h3>
                <p>View current trading positions</p>
                <button onclick="callTool('positions')">Run Tool</button>
            </div>

            <div class="tool">
                <h3>💰 Get Margins</h3>
                <p>Check available balance</p>
                <select id="segment" class="input-field">
                    <option value="equity">Equity</option>
                    <option value="commodity">Commodity</option>
                </select>
                <button onclick="callTool('margins')">Run Tool</button>
            </div>

            <div class="tool">
                <h3>📊 Get Quote</h3>
                <p>Get live price for stocks</p>
                <input type="text" id="quote_symbol" class="input-field" placeholder="NSE:INFY" value="NSE:INFY">
                <button onclick="callTool('quote')">Run Tool</button>
            </div>

            <div class="tool">
                <h3>🛒 Place Order</h3>
                <p>Buy or sell stocks</p>
                <input type="text" id="order_symbol" class="input-field" placeholder="INFY" value="INFY">
                <select id="transaction_type" class="input-field">
                    <option value="BUY">BUY</option>
                    <option value="SELL">SELL</option>
                </select>
                <input type="number" id="quantity" class="input-field" placeholder="Quantity" value="1">
                <select id="order_type" class="input-field">
                    <option value="MARKET">MARKET</option>
                    <option value="LIMIT">LIMIT</option>
                </select>
                <input type="number" id="price" class="input-field" placeholder="Price (for LIMIT)" step="0.01">
                <button onclick="callTool('order')">Place Order</button>
            </div>

        </div>
    </div>

    <div class="container">
        <h2>📋 Tool Result</h2>
        <div id="result">Click a tool button to see results...</div>
    </div>

    <script>
        async function callTool(tool) {
            const resultDiv = document.getElementById('result');
            resultDiv.textContent = '⏳ Loading...';

            let data = { tool: tool };

            if (tool === 'margins') {
                data.segment = document.getElementById('segment').value;
            } else if (tool === 'quote') {
                data.instruments = [document.getElementById('quote_symbol').value];
            } else if (tool === 'order') {
                data.symbol = document.getElementById('order_symbol').value;
                data.transaction_type = document.getElementById('transaction_type').value;
                data.quantity = parseInt(document.getElementById('quantity').value);
                data.order_type = document.getElementById('order_type').value;
                const price = document.getElementById('price').value;
                if (price) data.price = parseFloat(price);
            }

            try {
                const response = await fetch('/api/call_tool', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                resultDiv.textContent = JSON.stringify(result, null, 2);
            } catch (error) {
                resultDiv.textContent = 'Error: ' + error.message;
            }
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Main inspector page"""
    return render_template_string(
        HTML_TEMPLATE,
        authenticated=KiteConfig.is_authenticated()
    )


@app.route('/api/call_tool', methods=['POST'])
def api_call_tool():
    """API endpoint to call Kite tools"""
    data = request.json
    tool = data.get('tool')

    if not KiteConfig.is_authenticated() and tool != 'login':
        return jsonify({"success": False, "error": "Not authenticated"})

    result = None

    if tool == 'profile':
        result = kite_tools.get_profile()
    elif tool == 'holdings':
        result = kite_tools.get_holdings()
    elif tool == 'positions':
        result = kite_tools.get_positions()
    elif tool == 'margins':
        result = kite_tools.get_margins(data.get('segment', 'equity'))
    elif tool == 'quote':
        result = kite_tools.get_quote(data.get('instruments', []))
    elif tool == 'order':
        result = kite_tools.place_order(
            symbol=data['symbol'],
            exchange='NSE',
            transaction_type=data['transaction_type'],
            quantity=data['quantity'],
            order_type=data.get('order_type', 'MARKET'),
            product='CNC',
            price=data.get('price')
        )
    else:
        result = {"success": False, "error": "Unknown tool"}

    return jsonify(result)


if __name__ == '__main__':
    print("\n🎨 Kite MCP Visual Inspector")
    print("=" * 60)
    print(f"🌐 Open browser: http://127.0.0.1:5555")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5555, debug=False)
