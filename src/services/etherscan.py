from fastapi import APIRouter, HTTPException
import requests
from datetime import datetime

router = APIRouter(prefix="/etherscan", tags=["Etherscan"])

TOKEN_ADDRESSES = {
    "OUSG": "0x1b19c19393e2d034d8ff31ff34c81252fcbbee92",
    "USDY": "0x96f6ef951840721adbf46ac996b59e0235cb985c",
    "OMMF": "0x27c4d5a127c6c4abafd6b6e3b8f2ad8f93805aef",
}

BRIDGE_ADDRESSES = {
    "OUSG_bridge": "0x7d623c06b3d31a1a47e3512cd69a63a75f9e9c34",
    "USDY_bridge": "0x5e3f2c4c09a6bb482f0b1b34f4a83f6fb5d1c891",
}

@router.get("/txlist/{address}")
def get_tx_list(address: str):
    """
    Get transaction list for an address using Ethplorer (no API key required, use 'freekey').
    Direct URL: https://api.ethplorer.io/getAddressHistory/{address}?apiKey=freekey&type=transfer
    """
    url = f"https://api.ethplorer.io/getAddressHistory/{address}?apiKey=freekey&type=transfer"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from Ethplorer")
    return response.json()

@router.get("/token_txs/{token_symbol}")
def get_token_transactions(token_symbol: str):
    """
    Get token transactions for a specific RWA token using Ethplorer.
    Direct URL: https://api.ethplorer.io/getAddressHistory/{token_address}?apiKey=freekey&type=transfer
    """
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    token_address = TOKEN_ADDRESSES[token_symbol]
    url = f"https://api.ethplorer.io/getAddressHistory/{token_address}?apiKey=freekey&type=transfer"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from Ethplorer")
    return response.json()

@router.get("/token_holders/{token_symbol}")
def get_token_holders(token_symbol: str):
    """
    Get token holders for a specific RWA token using Ethplorer.
    Direct URL: https://api.ethplorer.io/getTopTokenHolders/{token_address}?apiKey=freekey&limit=100
    """
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    token_address = TOKEN_ADDRESSES[token_symbol]
    url = f"https://api.ethplorer.io/getTopTokenHolders/{token_address}?apiKey=freekey&limit=100"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from Ethplorer")
    return response.json()

@router.get("/bridge_activity/{token_symbol}")
def get_bridge_activity(token_symbol: str):
    """
    Get bridge activity for a specific RWA token using Ethplorer.
    Direct URL: https://api.ethplorer.io/getAddressHistory/{bridge_address}?apiKey=freekey&type=transfer
    """
    bridge_key = f"{token_symbol}_bridge"
    if bridge_key not in BRIDGE_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Bridge for {token_symbol} not found")
    bridge_address = BRIDGE_ADDRESSES[bridge_key]
    url = f"https://api.ethplorer.io/getAddressHistory/{bridge_address}?apiKey=freekey&type=transfer"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from Ethplorer")
    return response.json()

@router.get("/contract_calls/{token_symbol}")
def get_contract_calls(token_symbol: str):
    """
    Get contract call frequency for a specific RWA token using Ethplorer.
    Groups txs by date.
    """
    if token_symbol not in TOKEN_ADDRESSES:
        raise HTTPException(status_code=404, detail=f"Token {token_symbol} not found")
    token_address = TOKEN_ADDRESSES[token_symbol]
    url = f"https://api.ethplorer.io/getAddressHistory/{token_address}?apiKey=freekey&type=transfer"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from Ethplorer")
    data = response.json()
    txs = data.get("operations", [])
    tx_by_date = {}
    for tx in txs:
        ts = tx.get("timestamp")
        if ts:
            date_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
            tx_by_date[date_str] = tx_by_date.get(date_str, 0) + 1
    daily_calls = [{"date": d, "calls": c} for d, c in sorted(tx_by_date.items())]
    return {
        "token": token_symbol,
        "contract_address": token_address,
        "total_calls": len(txs),
        "daily_calls": daily_calls
    }