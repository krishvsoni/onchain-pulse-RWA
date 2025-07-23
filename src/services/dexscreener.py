from fastapi import APIRouter, HTTPException
import requests
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/dexscreener", tags=["Dexscreener"])

DEXSCREENER_API_KEY = os.getenv("DEXSCREENER_API_KEY")

# Token addresses for common RWA tokens
TOKEN_ADDRESSES = {
    "OUSG": "0x1b19c19393e2d034d8ff31ff34c81252fcbbee92",  # Ondo U.S. Government Bond
    "USDY": "0x96f6ef951840721adbf46ac996b59e0235cb985c",  # Ondo Short-Term U.S. Treasury
    "OMMF": "0x27c4d5a127c6c4abafd6b6e3b8f2ad8f93805aef",  # Ondo Money Market Fund
}

@router.get("/token/{chain}/{pair_address}")
def get_token_data(chain: str, pair_address: str):
    """Get data for a specific token pair"""
    url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{pair_address}"
    headers = {}
    if DEXSCREENER_API_KEY:
        headers["X-API-KEY"] = DEXSCREENER_API_KEY
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from Dexscreener")
    return response.json()

@router.get("/token/{token_symbol}")
def get_token_by_symbol(token_symbol: str):
    """Get data for a token by its symbol"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    headers = {}
    if DEXSCREENER_API_KEY:
        headers["X-API-KEY"] = DEXSCREENER_API_KEY
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from Dexscreener")
    return response.json()

@router.get("/liquidity/{token_symbol}")
def get_token_liquidity(token_symbol: str):
    """Get liquidity data for a token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    headers = {}
    if DEXSCREENER_API_KEY:
        headers["X-API-KEY"] = DEXSCREENER_API_KEY
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from Dexscreener")
    
    data = response.json()
    
    # Extract liquidity information from pairs
    liquidity_data = []
    if "pairs" in data and data["pairs"]:
        for pair in data["pairs"]:
            liquidity_data.append({
                "pair": pair.get("pairAddress"),
                "dex": pair.get("dexId"),
                "chain": pair.get("chainId"),
                "liquidity_usd": pair.get("liquidity", {}).get("usd"),
                "volume_24h": pair.get("volume", {}).get("h24"),
                "price_usd": pair.get("priceUsd"),
                "price_change_24h": pair.get("priceChange", {}).get("h24")
            })
    
    return {
        "token": token_symbol,
        "address": token_address,
        "liquidity_data": liquidity_data
    }