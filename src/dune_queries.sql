-- Dune SQL queries for OnChain Pulse dashboard

-- Krish Soni
-- github.com/krishvsoni

-- 1. Overview (TVL, Volume, Token-level TVL)
-- Total TVL and 24h Volume for all RWA tokens
SELECT SUM(tvl) AS total_tvl, SUM(volume_24h) AS total_volume FROM rwa_token_stats WHERE block_time >= NOW() - INTERVAL '1 day';

-- TVL by Token (Pie Chart)
SELECT token_symbol, SUM(tvl) AS tvl FROM rwa_token_stats WHERE block_time >= NOW() - INTERVAL '1 day' GROUP BY token_symbol ORDER BY tvl DESC;

-- 2. Token Analysis (Price, Volume, Volatility)
-- Price history for a token
SELECT block_time AS date, price_usd FROM token_prices WHERE token_address = '<TOKEN_ADDRESS>' AND block_time >= NOW() - INTERVAL '<DAYS> days' ORDER BY block_time;

-- Trading volume for a token
SELECT block_time AS date, volume_usd FROM token_volumes WHERE token_address = '<TOKEN_ADDRESS>' AND block_time >= NOW() - INTERVAL '<DAYS> days' ORDER BY block_time;

-- 3. Wallet Distribution (Holders, Whale Wallets)
-- Daily unique holders
SELECT DATE(block_time) AS date, COUNT(DISTINCT wallet_address) AS holders FROM token_transfers WHERE token_address = '<TOKEN_ADDRESS>' AND block_time >= NOW() - INTERVAL '180 days' GROUP BY DATE(block_time) ORDER BY date;

-- Whale wallets (>1% supply)
SELECT wallet_address, balance FROM token_balances WHERE token_address = '<TOKEN_ADDRESS>' AND balance > (SELECT SUM(balance)*0.01 FROM token_balances WHERE token_address = '<TOKEN_ADDRESS>');

-- 4. Bridge Activity
-- Daily inflow/outflow for a token
SELECT DATE(block_time) AS date, SUM(CASE WHEN direction = 'in' THEN amount ELSE 0 END) AS inflow, SUM(CASE WHEN direction = 'out' THEN amount ELSE 0 END) AS outflow FROM bridge_transfers WHERE token_address = '<TOKEN_ADDRESS>' AND block_time >= NOW() - INTERVAL '<DAYS> days' GROUP BY DATE(block_time) ORDER BY date;

-- 5. DeFi Usage (TVL by Protocol)
-- TVL by protocol for a token
SELECT protocol, SUM(tvl) AS tvl FROM defi_protocol_tvl WHERE token_address = '<TOKEN_ADDRESS>' AND block_time >= NOW() - INTERVAL '<DAYS> days' GROUP BY protocol ORDER BY tvl DESC;

-- 6. Competitor Analysis (RWA protocols)
-- TVL by RWA protocol
SELECT protocol_name, SUM(tvl) AS tvl FROM rwa_protocols WHERE block_time >= NOW() - INTERVAL '1 day' GROUP BY protocol_name ORDER BY tvl DESC;

-- 7. Market Maker Activity (Volume, Buy/Sell, Liquidity)
-- Daily market maker volume
SELECT mm_name, DATE(block_time) AS date, SUM(volume) AS total_volume, SUM(buy_volume) AS buy_volume, SUM(sell_volume) AS sell_volume, SUM(trades) AS trades FROM market_maker_activity WHERE token_address = '<TOKEN_ADDRESS>' AND block_time >= NOW() - INTERVAL '<DAYS> days' GROUP BY mm_name, DATE(block_time) ORDER BY mm_name, date;

-- Liquidity by pool for a market maker
SELECT mm_name, dex, pool, liquidity FROM mm_liquidity WHERE token_address = '<TOKEN_ADDRESS>';

-- 8. DEX Screener (Pools, Liquidity)
-- DEX pools for a token
SELECT pool_name, dex, liquidity, volume_24h FROM dex_pools WHERE token_address = '<TOKEN_ADDRESS>' ORDER BY liquidity DESC;

-- 9. Etherscan (Recent Transactions)
-- Recent token transactions
SELECT * FROM token_transfers WHERE token_address = '<TOKEN_ADDRESS>' ORDER BY block_time DESC LIMIT 100;

