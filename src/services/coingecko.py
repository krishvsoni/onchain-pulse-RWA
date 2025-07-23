from fastapi import APIRouter, HTTPException
import requests
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/coingecko", tags=["CoinGecko"])

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

# Token IDs for common RWA tokens
TOKEN_IDS = {
    "OUSG": "ondo-us-government-bond",
    "USDY": "ondo-finance-usdy",
    "OMMF": "ondo-money-market-fund"
}

def get_headers():
    headers = {}
    if COINGECKO_API_KEY:
        headers["x-cg-pro-api-key"] = COINGECKO_API_KEY
    return headers

@router.get("/price/{token_symbol}")
def get_price(token_symbol: str, vs_currency: str = "usd"):
    """Get current price of a token by symbol"""
    if token_symbol not in TOKEN_IDS:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    coin_id = TOKEN_IDS[token_symbol]
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={vs_currency}"
    
    response = requests.get(url, headers=get_headers())
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from CoinGecko")
    
    return response.json()

@router.get("/market_chart/{token_symbol}")
def get_market_chart(token_symbol: str, vs_currency: str = "usd", days: int = 30):
    """Get historical market data including price, market cap, and volume"""
    if token_symbol not in TOKEN_IDS:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    coin_id = TOKEN_IDS[token_symbol]
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={vs_currency}&days={days}"
    
    response = requests.get(url, headers=get_headers())
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from CoinGecko")
    
    return response.json()

@router.get("/token_info/{token_symbol}")
def get_token_info(token_symbol: str):
    """Get detailed information about a token"""
    if token_symbol not in TOKEN_IDS:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    coin_id = TOKEN_IDS[token_symbol]
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false"
    
    response = requests.get(url, headers=get_headers())
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from CoinGecko")
    
    return response.json()

@router.get("/compare_tokens")
def compare_tokens(vs_currency: str = "usd"):
    """Compare all tracked RWA tokens"""
    tokens_data = []
    
    for symbol, coin_id in TOKEN_IDS.items():
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false"
        
        response = requests.get(url, headers=get_headers())
        if response.status_code != 200:
            continue
        
        data = response.json()
        
        token_data = {
            "symbol": symbol,
            "name": data.get("name"),
            "current_price": data.get("market_data", {}).get("current_price", {}).get(vs_currency),
            "market_cap": data.get("market_data", {}).get("market_cap", {}).get(vs_currency),
            "total_volume": data.get("market_data", {}).get("total_volume", {}).get(vs_currency),
            "price_change_24h": data.get("market_data", {}).get("price_change_percentage_24h"),
            "price_change_7d": data.get("market_data", {}).get("price_change_percentage_7d"),
            "price_change_30d": data.get("market_data", {}).get("price_change_percentage_30d")
        }
        
        tokens_data.append(token_data)
    
    return {
        "tokens": tokens_data,
        "vs_currency": vs_currency
    }

@router.get("/historical_comparison")
def historical_comparison(days: int = 30, vs_currency: str = "usd"):
    """Get historical price comparison for all tracked tokens"""
    comparison_data = {}
    
    for symbol, coin_id in TOKEN_IDS.items():
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={vs_currency}&days={days}"
        
        response = requests.get(url, headers=get_headers())
        if response.status_code != 200:
            continue
        
        data = response.json()
        
        # Extract price data
        if "prices" in data:
            comparison_data[symbol] = data["prices"]
    
    return comparison_data