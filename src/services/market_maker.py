from fastapi import APIRouter, HTTPException
import requests
import os
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/market_maker", tags=["Market Maker Activity"])

# Mock market maker addresses for demonstration
MARKET_MAKER_ADDRESSES = {
    "MM1": "0x123456789abcdef123456789abcdef123456789a",
    "MM2": "0x987654321fedcba987654321fedcba987654321f",
    "MM3": "0xabcdef123456789abcdef123456789abcdef1234",
}

@router.get("/activity")
def get_market_maker_activity(days: int = 30):
    """Get market maker activity data"""
    # In production, this would query data from exchanges or on-chain sources
    # For now, we'll generate mock data
    
    # Generate dates for the past N days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate mock data
    import random
    random.seed(42)  # For reproducible results
    
    mm_data = {}
    
    for mm_name in MARKET_MAKER_ADDRESSES.keys():
        daily_data = []
        
        for date in date_range:
            # Generate random activity values with weekly patterns
            weekday = date.weekday()
            # Less activity on weekends
            base_volume = 500000 if weekday < 5 else 300000
            
            # Add some randomness
            daily_volume = max(100000, base_volume + random.randint(-150000, 200000))
            
            # Generate buy/sell ratio
            buy_percentage = random.uniform(0.4, 0.6)
            buy_volume = daily_volume * buy_percentage
            sell_volume = daily_volume * (1 - buy_percentage)
            
            daily_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "total_volume": round(daily_volume, 2),
                "buy_volume": round(buy_volume, 2),
                "sell_volume": round(sell_volume, 2),
                "trades": random.randint(50, 200)
            })
        
        mm_data[mm_name] = daily_data
    
    return mm_data

@router.get("/liquidity_provision")
def get_liquidity_provision():
    """Get liquidity provision data by market makers"""
    # In production, this would query data from DEXes or other sources
    # For now, we'll return mock data
    
    return {
        "MM1": {
            "total_liquidity": 12500000,
            "pools": [
                {"dex": "Curve", "pool": "OUSG/USDC", "liquidity": 5500000},
                {"dex": "Uniswap", "pool": "OUSG/ETH", "liquidity": 3500000},
                {"dex": "Curve", "pool": "USDY/USDC", "liquidity": 3500000}
            ]
        },
        "MM2": {
            "total_liquidity": 9800000,
            "pools": [
                {"dex": "Curve", "pool": "OUSG/USDC", "liquidity": 4200000},
                {"dex": "Uniswap", "pool": "USDY/ETH", "liquidity": 2800000},
                {"dex": "Curve", "pool": "USDY/USDC", "liquidity": 2800000}
            ]
        },
        "MM3": {
            "total_liquidity": 7500000,
            "pools": [
                {"dex": "Curve", "pool": "OUSG/USDC", "liquidity": 3000000},
                {"dex": "Uniswap", "pool": "OUSG/ETH", "liquidity": 2500000},
                {"dex": "Curve", "pool": "USDY/USDC", "liquidity": 2000000}
            ]
        }
    }

@router.get("/spread_analysis/{token_symbol}")
def get_spread_analysis(token_symbol: str, days: int = 30):
    """Get bid-ask spread analysis for a specific token"""
    # Generate dates for the past N days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate mock data
    import random
    random.seed(42)  # For reproducible results
    
    spread_data = []
    
    # Base spread depends on token
    if token_symbol == "OUSG":
        base_spread = 0.05  # 5 basis points
    elif token_symbol == "USDY":
        base_spread = 0.07  # 7 basis points
    else:
        base_spread = 0.10  # 10 basis points
    
    for date in date_range:
        # Add some randomness to the spread
        daily_spread = max(0.01, base_spread + random.uniform(-0.02, 0.03))
        
        # Generate volume data
        daily_volume = random.uniform(800000, 2500000)
        
        spread_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "avg_spread_bps": round(daily_spread * 100, 2),  # Convert to basis points
            "min_spread_bps": round(max(0.01, daily_spread * 0.7) * 100, 2),
            "max_spread_bps": round(daily_spread * 1.3 * 100, 2),
            "volume": round(daily_volume, 2)
        })
    
    return {
        "token": token_symbol,
        "data": spread_data
    }