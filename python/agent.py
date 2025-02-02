import os
from typing import Dict, List, Tuple
import json
from dotenv import load_dotenv
import numpy as np
from collections import defaultdict
from moralis import sol_api

# Load environment variables
load_dotenv()

class KOLAnalyzer:
    def __init__(self):
        self.total_shares_outstanding = 1000000  # Initial shares outstanding
        self.liabilities = 1000  # Initial liabilities (e.g., management fees)
        self.api_key = os.getenv('MORALIS_API_KEY')
        if not self.api_key:
            raise ValueError("MORALIS_API_KEY not found in environment variables")
        
    def get_token_price(self, address: str) -> float:
        """Get token price from Moralis API."""
        try:
            params = {
                "network": "mainnet",
                "address": address
            }
            result = sol_api.token.get_token_price(
                api_key=self.api_key,
                params=params
            )
            return float(result.get('usdPrice', 0))
        except Exception as e:
            print(f"Error fetching price for {address}: {e}")
            return 0.0
        
    def analyze_holdings(self, kol_data: Dict) -> Tuple[Dict, Dict, Dict, float]:
        """Analyze KOL holdings and create weighted portfolios."""
        kols = kol_data['KOLs']
        
        # Calculate weighted holdings based on followers
        total_followers = sum(kol['followers'] for kol in kols)
        weighted_holdings = defaultdict(float)
        mention_count = defaultdict(int)
        mention_amounts = defaultdict(float)
        
        for kol in kols:
            weight = kol['followers'] / total_followers
            for coin, data in kol['coins'].items():
                mentions = data['mentions']
                weighted_holdings[coin] += mentions * weight
                mention_count[coin] += 1
                mention_amounts[coin] += mentions
        
        # Sort coins by weighted holdings
        sorted_holdings = dict(sorted(
            weighted_holdings.items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        return sorted_holdings, mention_count, mention_amounts, total_followers
    
    def calculate_allocations(self, kol_data: Dict) -> Dict:
        """Calculate ETF allocations based on KOL data using mathematical formulas."""
        # Get basic metrics
        weighted_holdings, mention_count, mention_amounts, total_followers = self.analyze_holdings(kol_data)
        total_kols = len(kol_data['KOLs'])
        
        # Calculate scores for each coin
        coin_scores = {}
        max_mentions = max(mention_count.values())
        max_amount = max(mention_amounts.values())
        
        for coin, weighted_value in weighted_holdings.items():
            # Normalize components
            holding_score = weighted_value / max(weighted_holdings.values())  # Normalize holdings to 0-1
            
            # New mention score combines frequency and amount
            mention_frequency = mention_count[coin] / max_mentions  # How many KOLs mention it
            mention_amount = mention_amounts[coin] / max_amount     # How much they mention it
            mention_score = (mention_frequency * 0.6 + mention_amount * 0.4)  # Weight frequency higher than amount
            
            # Combined score (50% weight on holdings, 50% on mentions)
            coin_scores[coin] = (0.5 * holding_score + 0.5 * mention_score)
        
        # Convert scores to allocations
        total_score = sum(coin_scores.values())
        raw_allocations = {
            coin: (score / total_score) * 100 
            for coin, score in coin_scores.items()
        }
        
        # Adjust allocations to meet constraints (5% min, 40% max)
        min_allocation = 5
        max_allocation = 40
        
        # First pass: cap at maximum
        allocations = {
            coin: min(alloc, max_allocation)
            for coin, alloc in raw_allocations.items()
        }
        
        # Second pass: ensure minimum and normalize to 100%
        deficit = sum(
            max(min_allocation - alloc, 0)
            for alloc in allocations.values()
        )
        
        excess = sum(allocations.values()) - (100 - deficit)
        if excess > 0:
            # Reduce proportionally from coins above minimum
            above_min = {
                coin: alloc - min_allocation
                for coin, alloc in allocations.items()
                if alloc > min_allocation
            }
            reduction_factor = (sum(above_min.values()) - excess) / sum(above_min.values())
            
            final_allocations = {
                coin: max(
                    min_allocation,
                    min_allocation + (alloc - min_allocation) * reduction_factor
                )
                for coin, alloc in allocations.items()
            }
        else:
            final_allocations = allocations
        
        # Round to integers while maintaining 100% total
        rounded_allocations = []
        remaining = 100
        for coin in sorted(final_allocations.keys()):
            if coin == list(final_allocations.keys())[-1]:
                # Last coin gets whatever's left to ensure 100% total
                allocation = remaining
            else:
                allocation = round(final_allocations[coin])
                remaining -= allocation
            
            rounded_allocations.append({
                "name": coin,
                "allocation": int(allocation)
            })
        
        return {"coins": rounded_allocations}

    def calculate_nav(self, allocations: Dict, coin_data: Dict) -> Dict:
        """Calculate the Net Asset Value of the portfolio using real-time prices."""
        # Create a mapping of coin_id to price using Moralis API
        coin_prices = {}
        for coin in coin_data['coins']:
            price = self.get_token_price(coin['coin_address'])
            coin_prices[coin['coin_id']] = price
        
        # Calculate total portfolio value
        total_value = 0
        holdings_value = {}
        
        for coin in allocations['coins']:
            coin_id = coin['name'].lower()
            if coin_id in coin_prices:
                price = coin_prices[coin_id]
                allocation_decimal = coin['allocation'] / 100.0
                value = self.total_shares_outstanding * allocation_decimal * price
                holdings_value[coin_id] = {
                    'price': price,
                    'allocation': coin['allocation'],
                    'value': value
                }
                total_value += value
        
        # Calculate NAV
        nav = (total_value - self.liabilities) / self.total_shares_outstanding if self.total_shares_outstanding > 0 else 0
        
        return {
            'nav': round(nav, 4),
            'total_value': round(total_value, 2),
            'holdings_value': holdings_value,
            'liabilities': self.liabilities,
            'shares_outstanding': self.total_shares_outstanding
        }

def main():
    # Read KOL data from JSON file
    try:
        with open('kol_data.json', 'r') as f:
            kol_data = json.load(f)
    except FileNotFoundError:
        print("Error: kol_data.json file not found!")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in kol_data.json!")
        return
    
    analyzer = KOLAnalyzer()
    
    # Calculate allocations
    allocations = analyzer.calculate_allocations(kol_data)
    print("\nCalculated Allocations:")
    print(json.dumps(allocations, indent=2))

    # Read coin data from JSON file
    try:
        with open('coin_data.json', 'r') as f:
            coin_data = json.load(f)
    except FileNotFoundError:
        print("Error: coin_data.json file not found!")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in coin_data.json!")
        return

    # Calculate NAV
    nav_data = analyzer.calculate_nav(allocations, coin_data)
    print("\nCalculated NAV:")
    print(json.dumps(nav_data, indent=2))

if __name__ == "__main__":
    main()