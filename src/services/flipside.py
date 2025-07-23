from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
import os
import httpx
import json
import pandas as pd
import asyncio
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/flipside", tags=["Flipside Crypto"])
FLIPSIDE_API_KEY = os.getenv("FLIPSIDE_API_KEY")
MCP_SSE_URL = os.getenv("FLIPSIDE_MCP_URL")

# Cache for query results
query_cache = {}

# Token addresses for common RWA tokens
TOKEN_ADDRESSES = {
    "OUSG": "0x1b19c19393e2d034d8ff31ff34c81252fcbbee92",  # Ondo U.S. Government Bond
    "USDY": "0x96f6ef951840721adbf46ac996b59e0235cb985c",  # Ondo Short-Term U.S. Treasury
    "OMMF": "0x27c4d5a127c6c4abafd6b6e3b8f2ad8f93805aef",  # Ondo Money Market Fund
}

@router.get("/stream")
async def stream_data():
    """Stream data from Flipside MCP"""
    if not MCP_SSE_URL:
        raise HTTPException(status_code=500, detail="Flipside MCP URL not configured")
    
    async def event_generator():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", MCP_SSE_URL) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield line + "\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

async def run_query(query: str):
    """Run a SQL query on Flipside"""
    if not FLIPSIDE_API_KEY:
        raise HTTPException(status_code=500, detail="Flipside API key not configured")
    
    # Check cache first
    cache_key = hash(query)
    if cache_key in query_cache and (datetime.now() - query_cache[cache_key]["timestamp"]).total_seconds() < 3600:
        return query_cache[cache_key]["result"]
    
    url = "https://api.flipsidecrypto.com/api/v2/queries"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": FLIPSIDE_API_KEY
    }
    payload = {
        "sql": query,
        "ttlMinutes": 60
    }
    
    async with httpx.AsyncClient() as client:
        # Submit the query
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error submitting query to Flipside")
        
        query_data = response.json()
        query_id = query_data["token"]
        
        # Poll for results
        result_url = f"https://api.flipsidecrypto.com/api/v2/queries/{query_id}"
        max_attempts = 10
        attempts = 0
        
        while attempts < max_attempts:
            await asyncio.sleep(2)  # Wait before checking status
            attempts += 1
            
            response = await client.get(result_url, headers=headers)
            if response.status_code != 200:
                continue
            
            result_data = response.json()
            if result_data["status"] == "finished":
                # Cache the result
                query_cache[cache_key] = {
                    "timestamp": datetime.now(),
                    "result": result_data["results"]
                }
                return result_data["results"]
            elif result_data["status"] == "failed":
                raise HTTPException(status_code=500, detail="Query execution failed")
        
        raise HTTPException(status_code=504, detail="Query timed out")

@router.get("/token_transfers/{token_symbol}")
async def get_token_transfers(token_symbol: str, days: int = 30):
    """Get token transfers for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    query = f"""
    SELECT 
        block_timestamp::date as date,
        COUNT(*) as num_transfers,
        SUM(amount) as total_amount,
        COUNT(DISTINCT from_address) as unique_senders,
        COUNT(DISTINCT to_address) as unique_receivers
    FROM ethereum.core.ez_token_transfers
    WHERE contract_address = LOWER('{token_address}')
    AND block_timestamp >= CURRENT_DATE - {days}
    GROUP BY date
    ORDER BY date
    """
    
    results = await run_query(query)
    
    return {
        "token": token_symbol,
        "address": token_address,
        "transfers": results
    }

@router.get("/defi_usage/{token_symbol}")
async def get_defi_usage(token_symbol: str, days: int = 30):
    """Get DeFi usage data for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    query = f"""
    WITH token_interactions AS (
        SELECT 
            block_timestamp::date as date,
            origin_from_address as user_address,
            origin_to_address as protocol_address,
            COUNT(*) as num_interactions
        FROM ethereum.core.fact_transactions
        WHERE block_timestamp >= CURRENT_DATE - {days}
        AND (INPUT LIKE CONCAT('%', LOWER('{token_address}'), '%'))
        GROUP BY date, user_address, protocol_address
    )
    SELECT 
        date,
        COUNT(DISTINCT user_address) as unique_users,
        COUNT(DISTINCT protocol_address) as unique_protocols,
        SUM(num_interactions) as total_interactions
    FROM token_interactions
    GROUP BY date
    ORDER BY date
    """
    
    results = await run_query(query)
    
    return {
        "token": token_symbol,
        "address": token_address,
        "defi_usage": results
    }

@router.get("/wallet_growth/{token_symbol}")
async def get_wallet_growth(token_symbol: str, days: int = 180):
    """Get wallet growth data for a specific RWA token"""
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    
    token_address = TOKEN_ADDRESSES[token_symbol]
    
    query = f"""
    WITH daily_holders AS (
        SELECT 
            block_timestamp::date as date,
            COUNT(DISTINCT to_address) as new_holders
        FROM ethereum.core.ez_token_transfers
        WHERE contract_address = LOWER('{token_address}')
        AND block_timestamp >= CURRENT_DATE - {days}
        AND to_address NOT IN (
            SELECT DISTINCT to_address
            FROM ethereum.core.ez_token_transfers
            WHERE contract_address = LOWER('{token_address}')
            AND block_timestamp < CURRENT_DATE - {days}
        )
        GROUP BY date
    ),
    cumulative_holders AS (
        SELECT
            date,
            new_holders,
            SUM(new_holders) OVER (ORDER BY date) as total_holders
        FROM daily_holders
    )
    SELECT * FROM cumulative_holders
    ORDER BY date
    """
    
    results = await run_query(query)
    
    return {
        "token": token_symbol,
        "address": token_address,
        "wallet_growth": results
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
    
    query = f"""
    WITH token_data AS (
        SELECT 
            contract_address,
            block_timestamp::date as date,
            COUNT(*) as num_transfers,
            COUNT(DISTINCT from_address) as unique_senders,
            COUNT(DISTINCT to_address) as unique_receivers
        FROM ethereum.core.ez_token_transfers
        WHERE contract_address IN ({', '.join([f"LOWER('{addr}')" for addr in competitors.values()])})
        AND block_timestamp >= CURRENT_DATE - {days}
        GROUP BY contract_address, date
    )
    SELECT * FROM token_data
    ORDER BY contract_address, date
    """
    
    results = await run_query(query)
    
    # Map addresses back to symbols
    address_to_symbol = {addr.lower(): symbol for symbol, addr in competitors.items()}
    
    # Process results
    processed_results = []
    for row in results:
        row_dict = dict(row)
        row_dict["token"] = address_to_symbol.get(row_dict["contract_address"].lower(), "Unknown")
        processed_results.append(row_dict)
    
    return {
        "comparison": processed_results
    }
