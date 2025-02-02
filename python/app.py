from flask import Flask, render_template
import json
from agent import KOLAnalyzer

app = Flask(__name__)

def get_portfolio_data():
    try:
        # Read KOL data
        with open('kol_data.json', 'r') as f:
            kol_data = json.load(f)
        
        # Read coin data
        with open('coin_data.json', 'r') as f:
            coin_data = json.load(f)
            # Create a mapping of coin_id to coin_address
            coin_addresses = {coin['coin_id']: coin['coin_address'] for coin in coin_data['coins']}
        
        # Calculate allocations
        analyzer = KOLAnalyzer()
        allocations = analyzer.calculate_allocations(kol_data)
        
        # Add coin addresses to the allocations
        for coin in allocations['coins']:
            coin['address'] = coin_addresses.get(coin['name'].lower(), 'Address not found')
        
        # Calculate NAV
        nav_data = analyzer.calculate_nav(allocations, coin_data)
        
        # Format numbers for display
        for coin_id, data in nav_data['holdings_value'].items():
            data['price'] = "{:.2f}".format(data['price'])
            data['value'] = "{:.2f}".format(data['value'])
        
        # Combine allocations and NAV data
        return {
            'coins': allocations['coins'],
            'nav': "{:.4f}".format(nav_data['nav']),
            'total_value': "{:.2f}".format(nav_data['total_value']),
            'holdings_value': nav_data['holdings_value'],
            'liabilities': "{:.2f}".format(nav_data['liabilities']),
            'shares_outstanding': "{:,}".format(nav_data['shares_outstanding'])
        }
    except Exception as e:
        print(f"Error getting portfolio data: {e}")
        return {
            "coins": [], 
            "nav": "0.0000", 
            "total_value": "0.00", 
            "holdings_value": {}, 
            "liabilities": "0.00", 
            "shares_outstanding": "0"
        }
        
@app.route('/')
def index():
    portfolio_data = get_portfolio_data()
    return render_template('index.html', portfolio_data=portfolio_data)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
