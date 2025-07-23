from fastapi import FastAPI
from services import dune, flipside, dexscreener, coingecko, etherscan, rwa_tracker, market_maker, moralis, covalent
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
load_dotenv()

app = FastAPI(title="OnChain Pulse API", description="Analytics Dashboard for Tokenized Assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dune.router)
app.include_router(flipside.router)
app.include_router(dexscreener.router)
app.include_router(coingecko.router)
app.include_router(etherscan.router)
app.include_router(rwa_tracker.router)
app.include_router(market_maker.router)
app.include_router(moralis.router)
app.include_router(covalent.router)

@app.get("/")
def root():
    return {"message": "Welcome to OnChain Pulse API"}

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
