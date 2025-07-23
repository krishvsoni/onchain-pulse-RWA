from fastapi import APIRouter, HTTPException
import requests
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/moralis", tags=["Moralis"])
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2"

# Token addresses for common RWA tokens
TOKEN_ADDRESSES = {
    "OUSG": "0x1b19c19393e2d034d8ff31ff34c81252fcbbee92",  # Ondo U.S. Government Bond
    "USDY": "0x96f6ef951840721adbf46ac996b59e0235cb985c",  # Ondo Short-Term U.S. Treasury
    "OMMF": "0x27c4d5a127c6c4abafd6b6e3b8f2ad8f93805aef",  # Ondo Money Market Fund
}

# Bridge contract addresses
BRIDGE_ADDRESSES = {
    "OUSG_bridge": "0x7d623c06b3d31a1a47e3512cd69a63a75f9e9c34",
    "USDY_bridge": "0x5e3f2c4c09a6bb482f0b1b34f4a83f6fb5d1c891",
}


def get_moralis_headers():
    """Get headers for Moralis API requests"""
    return {
        "accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }


@router.get("/token_price/{token_symbol}")
async def get_token_price(token_symbol: str):
    """Get current token price from Moralis"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    url = f"{MORALIS_BASE_URL}/erc20/{token_address}/price?chain=eth"
    
    try:
        response = requests.get(url, headers=get_moralis_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching token price: {str(e)}")


@router.get("/token_transfers/{token_symbol}")
async def get_token_transfers(token_symbol: str, days: int = 30, limit: int = 100):
    """Get token transfers for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    url = f"{MORALIS_BASE_URL}/erc20/{token_address}/transfers?chain=eth&from_date={from_date}&limit={limit}"
    
    try:
        response = requests.get(url, headers=get_moralis_headers())
        response.raise_for_status()
        data = response.json()
        
        # Process and structure the data
        transfers = []
        for transfer in data.get("result", []):
            transfers.append({
                "transaction_hash": transfer.get("transaction_hash"),
                "from_address": transfer.get("from_address"),
                "to_address": transfer.get("to_address"),
                "value": transfer.get("value"),
                "block_timestamp": transfer.get("block_timestamp"),
            })
        
        return {
            "token": token_symbol,
            "address": token_address,
            "transfers": transfers
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching token transfers: {str(e)}")


@router.get("/wallet_nfts/{address}")
async def get_wallet_nfts(address: str, chain: str = "eth", limit: int = 100):
    """Get NFTs owned by a wallet address"""
    url = f"{MORALIS_BASE_URL}/{address}/nft?chain={chain}&format=decimal&limit={limit}"
    
    try:
        response = requests.get(url, headers=get_moralis_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching wallet NFTs: {str(e)}")


@router.get("/token_metadata/{token_symbol}")
async def get_token_metadata(token_symbol: str):
    """Get token metadata for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    url = f"{MORALIS_BASE_URL}/erc20/metadata?chain=eth&addresses={token_address}"
    
    try:
        response = requests.get(url, headers=get_moralis_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching token metadata: {str(e)}")


@router.get("/token_holders/{token_symbol}")
async def get_token_holders(token_symbol: str, limit: int = 100):
    """Get token holders for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    url = f"{MORALIS_BASE_URL}/erc20/{token_address}/holders?chain=eth&limit={limit}"
    
    try:
        response = requests.get(url, headers=get_moralis_headers())
        response.raise_for_status()
        
        data = response.json()
        holders = data.get("result", [])
        
        # Calculate total supply and holder distribution
        total_supply = sum(float(holder.get("balance", 0)) for holder in holders)
        
        # Categorize holders by balance size
        categories = {
            "whales": 0,  # > 1% of supply
            "large": 0,  # 0.1% - 1% of supply
            "medium": 0,  # 0.01% - 0.1% of supply
            "small": 0,  # < 0.01% of supply
        }
        
        for holder in holders:
            balance = float(holder.get("balance", 0))
            percentage = (balance / total_supply) * 100 if total_supply > 0 else 0
            
            if percentage > 1:
                categories["whales"] += 1
            elif percentage > 0.1:
                categories["large"] += 1
            elif percentage > 0.01:
                categories["medium"] += 1
            else:
                categories["small"] += 1
        
        return {
            "token": token_symbol,
            "address": token_address,
            "total_holders": len(holders),
            "total_supply": total_supply,
            "distribution": categories,
            "holders": holders
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching token holders: {str(e)}")


@router.get("/defi_stats/{token_symbol}")
async def get_defi_stats(token_symbol: str):
    """Get DeFi statistics for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    # This is a placeholder for actual DeFi stats integration
    # In a real implementation, you would query various DeFi protocols
    # to get TVL, volume, and other metrics for the token
    
    # For now, we'll return mock data
    mock_data = {
        "token": token_symbol,
        "address": token_address,
        "total_tvl": 75000000,
        "protocols": [
            {"name": "Curve Finance", "tvl": 32000000, "volume24h": 2800000, "apy": 3.8},
            {"name": "Aave", "tvl": 18000000, "volume24h": 1200000, "apy": 4.5},
            {"name": "Balancer", "tvl": 12000000, "volume24h": 850000, "apy": 4.2},
            {"name": "Uniswap", "tvl": 8000000, "volume24h": 350000, "apy": 3.5},
            {"name": "Compound", "tvl": 5000000, "volume24h": 0, "apy": 5.1}
        ]
    }
    
    return mock_data