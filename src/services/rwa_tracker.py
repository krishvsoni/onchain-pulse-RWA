from fastapi import APIRouter, HTTPException
import requests
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/rwa", tags=["RWA Tracker"])

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

# Token addresses for common RWA tokens
TOKEN_ADDRESSES = {
    "OUSG": "0x1b19c19393e2d034d8ff31ff34c81252fcbbee92",  # Ondo U.S. Government Bond
    "USDY": "0x96f6ef951840721adbf46ac996b59e0235cb985c",  # Ondo Short-Term U.S. Treasury
    "OMMF": "0x27c4d5a127c6c4abafd6b6e3b8f2ad8f93805aef",  # Ondo Money Market Fund
    # Add more tokens as needed
}

# Bridge contract addresses
BRIDGE_ADDRESSES = {
    "OUSG_bridge": "0x7d623c06b3d31a1a47e3512cd69a63a75f9e9c34",
    # Add more bridge addresses as needed
}

@router.get("/token_addresses")
def get_token_addresses():
    """Get the list of tracked RWA token addresses"""
    return TOKEN_ADDRESSES

@router.get("/wallet_distribution/{token_symbol}")
def get_wallet_distribution(token_symbol: str):
    """Get wallet distribution for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    # Call Etherscan API to get token holders
    url = f"https://api.etherscan.io/api?module=token&action=tokenholderlist&contractaddress={token_address}&page=1&offset=100&apikey={ETHERSCAN_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data["status"] != "1":
            # If Etherscan API is rate limited or returns an error, return mock data for now
            # In production, implement proper error handling and caching
            return {
                "whale_wallets": 5,  # Wallets with >1% of supply
                "institutional_wallets": 15,  # Wallets with 0.1-1% of supply
                "retail_wallets": 180,  # Wallets with <0.1% of supply
                "total_holders": 200,
                "concentration": {
                    "top_10_percent": 85.5,  # % of supply held by top 10% of wallets
                    "top_1_percent": 65.2,  # % of supply held by top 1% of wallets
                }
            }
        
        # Process the actual data
        holders = data["result"]
        total_holders = len(holders)
        
        # Sort holders by balance
        holders_df = pd.DataFrame(holders)
        holders_df["TokenBalance"] = holders_df["TokenBalance"].astype(float)
        holders_df = holders_df.sort_values(by="TokenBalance", ascending=False)
        
        # Calculate total supply
        total_supply = holders_df["TokenBalance"].sum()
        
        # Calculate percentages
        holders_df["percentage"] = holders_df["TokenBalance"] / total_supply * 100
        
        # Categorize wallets
        whale_wallets = len(holders_df[holders_df["percentage"] > 1])
        institutional_wallets = len(holders_df[(holders_df["percentage"] <= 1) & (holders_df["percentage"] > 0.1)])
        retail_wallets = len(holders_df[holders_df["percentage"] <= 0.1])
        
        # Calculate concentration
        top_10_percent_count = max(1, int(total_holders * 0.1))
        top_1_percent_count = max(1, int(total_holders * 0.01))
        
        top_10_percent_concentration = holders_df.iloc[:top_10_percent_count]["percentage"].sum()
        top_1_percent_concentration = holders_df.iloc[:top_1_percent_count]["percentage"].sum()
        
        return {
            "whale_wallets": whale_wallets,
            "institutional_wallets": institutional_wallets,
            "retail_wallets": retail_wallets,
            "total_holders": total_holders,
            "concentration": {
                "top_10_percent": round(top_10_percent_concentration, 2),
                "top_1_percent": round(top_1_percent_concentration, 2),
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/holders_growth/{token_symbol}")
def get_holders_growth(token_symbol: str, days: int = 30):
    """Get historical growth of token holders over time"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    # In a production environment, this would query a database with historical data
    # For now, we'll generate mock data
    
    # Generate dates for the past N days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate mock data with an upward trend
    if token_symbol == "OUSG":
        start_holders = 150
        growth_rate = 1.8  # Average 1.8 new holders per day
    elif token_symbol == "USDY":
        start_holders = 180
        growth_rate = 2.2  # Average 2.2 new holders per day
    else:
        start_holders = 120
        growth_rate = 1.5
    
    # Create the growth data with some randomness
    import random
    random.seed(42)  # For reproducible results
    
    holders_data = []
    current_holders = start_holders
    
    for date in date_range:
        # Add some randomness to the growth
        daily_growth = max(0, growth_rate + random.uniform(-1, 1.5))
        current_holders += daily_growth
        
        holders_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "holders": round(current_holders)
        })
    
    return {
        "token": token_symbol,
        "data": holders_data
    }

@router.get("/bridge_activity/{token_symbol}")
def get_bridge_activity(token_symbol: str, days: int = 30):
    """Get bridge activity (inflows/outflows) for a specific token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    bridge_key = f"{token_symbol}_bridge"
    if bridge_key not in BRIDGE_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Bridge for {token_symbol} not found")
    
    bridge_address = BRIDGE_ADDRESSES[bridge_key]
    
    # In production, this would query transaction data from Etherscan or a database
    # For now, we'll generate mock data
    
    # Generate dates for the past N days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate mock data
    bridge_data = []
    
    import random
    random.seed(42)  # For reproducible results
    
    for date in date_range:
        # Generate random inflow/outflow values
        inflow = random.uniform(10000, 50000) if random.random() > 0.2 else random.uniform(1000, 10000)
        outflow = random.uniform(8000, 40000) if random.random() > 0.3 else random.uniform(500, 8000)
        
        bridge_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "inflow": round(inflow, 2),
            "outflow": round(outflow, 2),
            "net_flow": round(inflow - outflow, 2)
        })
    
    return {
        "token": token_symbol,
        "bridge_address": bridge_address,
        "data": bridge_data
    }

@router.get("/tvl_history/{token_symbol}")
def get_tvl_history(token_symbol: str, days: int = 30):
    """Get historical Total Value Locked (TVL) for a specific token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    # Generate dates for the past N days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate mock data with an upward trend
    if token_symbol == "OUSG":
        start_tvl = 25000000  # $25M
        growth_factor = 1.005  # 0.5% daily growth on average
    elif token_symbol == "USDY":
        start_tvl = 35000000  # $35M
        growth_factor = 1.006  # 0.6% daily growth on average
    else:
        start_tvl = 15000000  # $15M
        growth_factor = 1.004  # 0.4% daily growth on average
    
    # Create the TVL data with some randomness
    import random
    random.seed(42)  # For reproducible results
    
    tvl_data = []
    current_tvl = start_tvl
    
    for date in date_range:
        # Add some randomness to the growth
        daily_factor = growth_factor + random.uniform(-0.004, 0.006)
        current_tvl *= daily_factor
        
        tvl_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "tvl": round(current_tvl, 2)
        })
    
    return {
        "token": token_symbol,
        "data": tvl_data
    }

@router.get("/defi_usage/{token_symbol}")
def get_defi_usage(token_symbol: str):
    """Get DeFi usage statistics for a specific token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    # In production, this would query data from various DeFi protocols
    # For now, we'll return mock data
    
    if token_symbol == "OUSG":
        return {
            "token": token_symbol,
            "defi_usage": [
                {"protocol": "Curve", "tvl": 12500000, "percentage": 45.5},
                {"protocol": "Aave", "tvl": 8200000, "percentage": 29.8},
                {"protocol": "Uniswap", "tvl": 3500000, "percentage": 12.7},
                {"protocol": "Others", "tvl": 3300000, "percentage": 12.0}
            ]
        }
    elif token_symbol == "USDY":
        return {
            "token": token_symbol,
            "defi_usage": [
                {"protocol": "Curve", "tvl": 18500000, "percentage": 52.9},
                {"protocol": "Aave", "tvl": 9800000, "percentage": 28.0},
                {"protocol": "Uniswap", "tvl": 4200000, "percentage": 12.0},
                {"protocol": "Others", "tvl": 2500000, "percentage": 7.1}
            ]
        }
    else:
        return {
            "token": token_symbol,
            "defi_usage": [
                {"protocol": "Curve", "tvl": 7500000, "percentage": 50.0},
                {"protocol": "Aave", "tvl": 4500000, "percentage": 30.0},
                {"protocol": "Uniswap", "tvl": 1500000, "percentage": 10.0},
                {"protocol": "Others", "tvl": 1500000, "percentage": 10.0}
            ]
        }

@router.get("/competitor_comparison")
def get_competitor_comparison():
    """Get comparison data between Ondo and competitors"""
    return {
        "market_share": [
            {"issuer": "Ondo Finance", "tvl": 75000000, "percentage": 42.6},
            {"issuer": "Matrixdock", "tvl": 58000000, "percentage": 33.0},
            {"issuer": "Backed Finance", "tvl": 32000000, "percentage": 18.2},
            {"issuer": "Others", "tvl": 11000000, "percentage": 6.2}
        ],
        "user_growth": {
            "Ondo Finance": [
                {"month": "Jan", "users": 120},
                {"month": "Feb", "users": 145},
                {"month": "Mar", "users": 180},
                {"month": "Apr", "users": 210},
                {"month": "May", "users": 250},
                {"month": "Jun", "users": 310}
            ],
            "Matrixdock": [
                {"month": "Jan", "users": 110},
                {"month": "Feb", "users": 125},
                {"month": "Mar", "users": 150},
                {"month": "Apr", "users": 170},
                {"month": "May", "users": 195},
                {"month": "Jun", "users": 230}
            ],
            "Backed Finance": [
                {"month": "Jan", "users": 80},
                {"month": "Feb", "users": 95},
                {"month": "Mar", "users": 115},
                {"month": "Apr", "users": 130},
                {"month": "May", "users": 150},
                {"month": "Jun", "users": 175}
            ]
        },
        "product_diversity": {
            "Ondo Finance": 3,  # Number of different RWA products
            "Matrixdock": 2,
            "Backed Finance": 1
        }
    }

@router.get("/contract_activity/{token_symbol}")
def get_contract_activity(token_symbol: str, days: int = 30):
    """Get smart contract call frequency over time"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    # Generate dates for the past N days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate mock data
    import random
    random.seed(42)  # For reproducible results
    
    activity_data = []
    
    for date in date_range:
        # Generate random activity values with weekly patterns
        weekday = date.weekday()
        # Less activity on weekends
        base_activity = 120 if weekday < 5 else 70
        
        # Add some randomness
        daily_activity = max(10, base_activity + random.randint(-30, 50))
        
        activity_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "transactions": daily_activity,
            "unique_callers": max(5, int(daily_activity * random.uniform(0.3, 0.5)))
        })
    
    return {
        "token": token_symbol,
        "contract_address": token_address,
        "data": activity_data
    }