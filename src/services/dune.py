from fastapi import APIRouter, HTTPException, BackgroundTasks
import requests
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/dune", tags=["Dune Analytics"])
DUNE_API_KEY = "Hg51zVbkmv3eg9ZLNbz18blUNEOIPLyS"

# Cache for query results
query_cache = {}

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

def get_dune_headers():
    """Get headers for Dune API requests"""
    return {
        "accept": "application/json",
        "Authorization": f"Bearer {DUNE_API_KEY}"
    }

async def execute_query(query_id: str, parameters: Dict[str, Any] = None):
    """Execute a query on Dune Analytics"""
    if not DUNE_API_KEY:
        raise HTTPException(status_code=500, detail="Dune API key not configured")
    
    # Check cache first
    cache_key = f"{query_id}_{json.dumps(parameters) if parameters else ''}"
    if cache_key in query_cache and (datetime.now() - query_cache[cache_key]["timestamp"]).total_seconds() < 3600:
        return query_cache[cache_key]["result"]
    
    headers = get_dune_headers()
    
    # Execute the query
    execution_url = f"https://api.dune.com/api/v1/query/{query_id}/execute"
    
    try:
        # If parameters are provided, include them in the request
        if parameters:
            response = requests.post(execution_url, headers=headers, json={"parameters": parameters})
        else:
            response = requests.post(execution_url, headers=headers)
            
        response.raise_for_status()
        execution_data = response.json()
        execution_id = execution_data["execution_id"]
        
        # Poll for results
        status_url = f"https://api.dune.com/api/v1/execution/{execution_id}/status"
        results_url = f"https://api.dune.com/api/v1/execution/{execution_id}/results"
        
        max_attempts = 20
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            # Check status
            status_response = requests.get(status_url, headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            if status_data["state"] == "QUERY_STATE_COMPLETED":
                # Get results
                results_response = requests.get(results_url, headers=headers)
                results_response.raise_for_status()
                results_data = results_response.json()
                
                # Cache the result
                query_cache[cache_key] = {
                    "timestamp": datetime.now(),
                    "result": results_data["result"]
                }
                
                return results_data["result"]
            elif status_data["state"] in ["QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"]:
                raise HTTPException(status_code=500, detail="Query execution failed")
            
            # Wait before checking again
            import time
            time.sleep(2)
        
        raise HTTPException(status_code=504, detail="Query execution timed out")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error executing Dune query: {str(e)}")

@router.get("/token_transfers/{token_symbol}")
async def get_token_transfers(token_symbol: str, days: int = 30):
    """Get token transfers for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    # Use a predefined Dune query ID for token transfers
    query_id = "3215678"  # Replace with actual Dune query ID for token transfers
    parameters = {
        "token_address": token_address,
        "days": days
    }
    
    results = await execute_query(query_id, parameters)
    
    return {
        "token": token_symbol,
        "address": token_address,
        "transfers": results["rows"]
    }

@router.get("/defi_usage/{token_symbol}")
async def get_defi_usage(token_symbol: str, days: int = 30):
    """Get DeFi usage data for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    # Use a predefined Dune query ID for DeFi usage
    query_id = "3215679"  # Replace with actual Dune query ID for DeFi usage
    parameters = {
        "token_address": token_address,
        "days": days
    }
    
    results = await execute_query(query_id, parameters)
    
    return {
        "token": token_symbol,
        "address": token_address,
        "defi_usage": results["rows"]
    }

@router.get("/wallet_growth/{token_symbol}")
async def get_wallet_growth(token_symbol: str, days: int = 180):
    """Get wallet growth data for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    # Use a predefined Dune query ID for wallet growth
    query_id = "3215680"  # Replace with actual Dune query ID for wallet growth
    parameters = {
        "token_address": token_address,
        "days": days
    }
    
    results = await execute_query(query_id, parameters)
    
    return {
        "token": token_symbol,
        "address": token_address,
        "wallet_growth": results["rows"]
    }

@router.get("/competitor_comparison")
async def get_competitor_comparison(days: int = 30):
    """Compare RWA tokens from different issuers"""
    # Define competitor tokens
    competitors = {
        "OUSG": "0x1b19c19393e2d034d8ff31ff34c81252fcbbee92",  # Ondo
        "USDY": "0x96f6ef951840721adbf46ac996b59e0235cb985c",  # Ondo
        "USYD": "0x6b175474e89094c44da98b954eedeac495271d0f",  # Matrixdock (using DAI as placeholder)
        "TBILL": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # Backed Finance (using USDC as placeholder)
    }
    
    # Use a predefined Dune query ID for competitor comparison
    query_id = "3215681"  # Replace with actual Dune query ID for competitor comparison
    parameters = {
        "token_addresses": list(competitors.values()),
        "days": days
    }
    
    results = await execute_query(query_id, parameters)
    
    # Map addresses back to symbols
    address_to_symbol = {addr.lower(): symbol for symbol, addr in competitors.items()}
    
    # Process results
    processed_results = []
    for row in results["rows"]:
        row_dict = dict(row)
        row_dict["token"] = address_to_symbol.get(row_dict["contract_address"].lower(), "Unknown")
        processed_results.append(row_dict)
    
    return {
        "comparison": processed_results
    }

@router.get("/run_query/{query_id}")
async def run_query(query_id: str, parameters: Dict[str, Any] = None):
    """Run a specific Dune query by ID"""
    results = await execute_query(query_id, parameters)
    return results