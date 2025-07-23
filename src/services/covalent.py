from fastapi import APIRouter, HTTPException
import requests
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/covalent", tags=["Covalent"])
COVALENT_API_KEY = os.getenv("COVALENT_API_KEY")
COVALENT_BASE_URL = "https://api.covalenthq.com/v1"

# Token addresses for common RWA tokens
TOKEN_ADDRESSES = {
    "OUSG": "0x1b19c19393e2d034d8ff31ff34c81252fcbbee92",  # Ondo U.S. Government Bond
    "USDY": "0x96f6ef951840721adbf46ac996b59e0235cb985c",  # Ondo Short-Term U.S. Treasury
    "OMMF": "0x27c4d5a127c6c4abafd6b6e3b8f2ad8f93805aef",  # Ondo Money Market Fund
}


def get_covalent_auth():
    """Get authentication for Covalent API requests"""
    return (COVALENT_API_KEY, "")


@router.get("/token_balances/{address}")
async def get_token_balances(address: str, chain_id: int = 1):
    """Get token balances for a specific address"""
    url = f"{COVALENT_BASE_URL}/{chain_id}/address/{address}/balances_v2/"
    
    try:
        response = requests.get(url, auth=get_covalent_auth())
        response.raise_for_status()
        data = response.json()
        
        if data.get("error"):
            raise HTTPException(status_code=500, detail=data.get("error_message", "Unknown error"))
        
        return data.get("data", {})
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching token balances: {str(e)}")


@router.get("/token_holders/{token_symbol}")
async def get_token_holders(token_symbol: str, chain_id: int = 1, page_size: int = 100):
    """Get token holders for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    url = f"{COVALENT_BASE_URL}/{chain_id}/tokens/{token_address}/token_holders/?page-size={page_size}"
    
    try:
        response = requests.get(url, auth=get_covalent_auth())
        response.raise_for_status()
        data = response.json()
        
        if data.get("error"):
            raise HTTPException(status_code=500, detail=data.get("error_message", "Unknown error"))
        
        # Process and structure the data
        result = data.get("data", {})
        items = result.get("items", [])
        
        # Calculate total supply and holder distribution
        total_supply = sum(float(item.get("balance", 0)) for item in items)
        
        # Categorize holders by balance size
        categories = {
            "whales": 0,  # > 1% of supply
            "large": 0,  # 0.1% - 1% of supply
            "medium": 0,  # 0.01% - 0.1% of supply
            "small": 0,  # < 0.01% of supply
        }
        
        for item in items:
            balance = float(item.get("balance", 0))
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
            "total_holders": len(items),
            "total_supply": total_supply,
            "distribution": categories,
            "holders": items
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching token holders: {str(e)}")


@router.get("/historical_portfolio/{address}")
async def get_historical_portfolio(address: str, chain_id: int = 1, days: int = 30):
    """Get historical portfolio value for a specific address"""
    url = f"{COVALENT_BASE_URL}/{chain_id}/address/{address}/portfolio_v2/"
    
    try:
        response = requests.get(url, auth=get_covalent_auth())
        response.raise_for_status()
        data = response.json()
        
        if data.get("error"):
            raise HTTPException(status_code=500, detail=data.get("error_message", "Unknown error"))
        
        # Filter for the requested time period
        result = data.get("data", {})
        items = result.get("items", [])
        
        # Calculate date threshold
        threshold_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Filter items by date
        filtered_items = [item for item in items if item.get("timestamp", "") >= threshold_date]
        
        return {
            "address": address,
            "chain_id": chain_id,
            "portfolio_history": filtered_items
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical portfolio: {str(e)}")


@router.get("/token_transfers/{token_symbol}")
async def get_token_transfers(token_symbol: str, chain_id: int = 1, page_size: int = 100):
    """Get token transfers for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    url = f"{COVALENT_BASE_URL}/{chain_id}/tokens/{token_address}/token_transfers/?page-size={page_size}"
    
    try:
        response = requests.get(url, auth=get_covalent_auth())
        response.raise_for_status()
        data = response.json()
        
        if data.get("error"):
            raise HTTPException(status_code=500, detail=data.get("error_message", "Unknown error"))
        
        return data.get("data", {})
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching token transfers: {str(e)}")


@router.get("/cross_chain_balances/{address}")
async def get_cross_chain_balances(address: str, chains: List[int] = None):
    """Get token balances across multiple chains for a specific address"""
    if chains is None:
        chains = [1, 137, 56, 43114]  # Ethereum, Polygon, BSC, Avalanche
    
    results = {}
    
    for chain_id in chains:
        try:
            url = f"{COVALENT_BASE_URL}/{chain_id}/address/{address}/balances_v2/"
            response = requests.get(url, auth=get_covalent_auth())
            response.raise_for_status()
            data = response.json()
            
            if not data.get("error"):
                results[chain_id] = data.get("data", {})
            else:
                results[chain_id] = {"error": data.get("error_message", "Unknown error")}
        except requests.exceptions.RequestException as e:
            results[chain_id] = {"error": str(e)}
    
    return {
        "address": address,
        "balances": results
    }


@router.get("/token_market_data/{token_symbol}")
async def get_token_market_data(token_symbol: str, chain_id: int = 1, days: int = 30):
    """Get market data for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    # Get token metadata
    metadata_url = f"{COVALENT_BASE_URL}/{chain_id}/tokens/{token_address}/"
    
    try:
        metadata_response = requests.get(metadata_url, auth=get_covalent_auth())
        metadata_response.raise_for_status()
        metadata_data = metadata_response.json()
        
        if metadata_data.get("error"):
            raise HTTPException(status_code=500, detail=metadata_data.get("error_message", "Unknown error"))
        
        # Get token price history
        price_url = f"{COVALENT_BASE_URL}/pricing/historical_by_addresses_v2/{chain_id}/USD/{token_address}/?days={days}"
        price_response = requests.get(price_url, auth=get_covalent_auth())
        price_response.raise_for_status()
        price_data = price_response.json()
        
        if price_data.get("error"):
            raise HTTPException(status_code=500, detail=price_data.get("error_message", "Unknown error"))
        
        # Combine the data
        return {
            "token": token_symbol,
            "address": token_address,
            "metadata": metadata_data.get("data", {}),
            "price_history": price_data.get("data", {})
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching token market data: {str(e)}")