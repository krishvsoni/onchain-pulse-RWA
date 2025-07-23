import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

st.set_page_config(
    page_title="OnChain Pulse: RWA Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"

st.sidebar.title("OnChain Pulse")
st.sidebar.subheader("RWA Analytics Dashboard")

token_options = ["OUSG", "USDY", "OMMF"]
selected_token = st.sidebar.selectbox("Select Token", token_options, key="sidebar_token_select")

time_period = st.sidebar.selectbox(
    "Select Time Period",
    ["7 Days", "30 Days", "90 Days", "180 Days", "1 Year"],
    index=1,
    key="sidebar_time_period_select"
)

time_period_days = {
    "7 Days": 7,
    "30 Days": 30,
    "90 Days": 90,
    "180 Days": 180,
    "1 Year": 365
}[time_period]

def format_number(num):
    if isinstance(num, (list, tuple, set)):
        if len(num) == 1:
            num = num[0]
        else:
            return str(num)
    try:
        n = float(num)
    except (ValueError, TypeError):
        return str(num)
    if n >= 1_000_000_000:
        return f"${n/1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"${n/1_000_000:.2f}M"
    elif n >= 1_000:
        return f"${n/1_000:.2f}K"
    else:
        return f"${n:.2f}"

page = st.sidebar.radio(
    "Select Page",
    [
        "Overview",
        "Token Analysis",
        "Wallet Distribution",
        "Bridge Activity",
        "DeFi Usage",
        "Competitor Analysis",
        "Market Maker Activity",
        "DEX Screener",
        "Etherscan"
    ]
)

if page == "DEX Screener":
    st.title("DEX Screener Analytics")
    st.info("Fivetran Webhook: For automated data sync, POST to `/webhook/fivetran` on your FastAPI backend after each sync. Configure this in your Fivetran dashboard.")
    dex_data = None
    try:
        dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{selected_token}"
        dex_resp = requests.get(dex_url)
        dex_data = dex_resp.json() if dex_resp.status_code == 200 else None
    except Exception as e:
        st.error(f"Error fetching DEX Screener data: {e}")
    if dex_data and "pools" in dex_data:
        pools_df = pd.DataFrame(dex_data["pools"])
        st.subheader(f"{selected_token} DEX Pools")
        st.dataframe(pools_df)
        if not pools_df.empty:
            fig = px.bar(
                pools_df,
                x="pool_name" if "pool_name" in pools_df else pools_df.columns[0],
                y="liquidity" if "liquidity" in pools_df else pools_df.columns[1],
                title=f"{selected_token} Liquidity by Pool"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No DEX Screener data available for this token.")

elif page == "Etherscan":
    st.title("Etherscan Analytics")
    st.info("Fivetran Webhook: For automated data sync, POST to `/webhook/fivetran` on your FastAPI backend after each sync. Configure this in your Fivetran dashboard.")
    eth_data = None
    etherscan_token_map = {
        "OUSG": "0x9d4643ecb8e6e3a0b6b6b6b6b6b6b6b6b6b6b6b6",  
        "USDY": "0x1234567890abcdef1234567890abcdef12345678",
        "OMMF": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
    }
    contract_address = etherscan_token_map.get(selected_token)
    etherscan_api_key = "52GSAIFED4DV5157ZT12Q5QASZ3NG7DBS5"  
    if contract_address:
        try:
            tx_url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract_address}&page=1&offset=100&sort=desc&apikey={etherscan_api_key}"
            tx_resp = requests.get(tx_url)
            tx_data = tx_resp.json() if tx_resp.status_code == 200 else None
        except Exception as e:
            tx_data = None
            st.error(f"Error fetching Etherscan transactions: {e}")
        if tx_data and tx_data.get("status") == "1":
            tx_df = pd.DataFrame(tx_data["result"])
            st.subheader(f"{selected_token} Recent Transactions")
            st.dataframe(tx_df.head(20))
            if not tx_df.empty and "value" in tx_df:
                fig = px.histogram(
                    tx_df,
                    x="value",
                    nbins=30,
                    title=f"{selected_token} Transaction Value Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No Etherscan transaction data available for this token.")
    else:
        st.warning("No contract address available for this token.")
    if eth_data and "transactions" in eth_data:
        tx_df = pd.DataFrame(eth_data["transactions"])
        st.subheader(f"{selected_token} Recent Transactions")
        st.dataframe(tx_df.head(20))
        if not tx_df.empty and "value" in tx_df:
            fig = px.histogram(
                tx_df,
                x="value",
                nbins=30,
                title=f"{selected_token} Transaction Value Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No Etherscan transaction data available for this token.")

token_options = ["OUSG", "USDY", "OMMF"]
selected_token = st.sidebar.selectbox("Select Token", token_options)

time_period = st.sidebar.selectbox(
    "Select Time Period",
    ["7 Days", "30 Days", "90 Days", "180 Days", "1 Year"],
    index=1
)

time_period_days = {
    "7 Days": 7,
    "30 Days": 30,
    "90 Days": 90,
    "180 Days": 180,
    "1 Year": 365
}[time_period]

def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def metric_card(title, value, delta=None, delta_suffix="%", help_text=None):
    with st.container():
        st.metric(title, value, delta=f"{delta}{delta_suffix}" if delta else None, help=help_text)

def format_number(num):
    if num >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"${num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"${num/1_000:.2f}K"
    else:
        return f"${num:.2f}"

if page == "Overview":
    st.title("OnChain Pulse: RWA Analytics Dashboard")
    st.subheader("Real-World Asset Tokens Overview")
    st.markdown("[Data Source: DefiLlama](https://defillama.com/) ")
    try:
        llama_url = "https://api.llama.fi/protocol/ondo-finance"
        llama_resp = requests.get(llama_url)
        llama_data = llama_resp.json() if llama_resp.status_code == 200 else None
    except Exception as e:
        llama_data = None
        st.error(f"Error fetching DefiLlama data: {e}")
    col1, col2, col3 = st.columns(3)
    if llama_data:
        tvl_val = llama_data.get("tvl", 0)
        if isinstance(tvl_val, (list, tuple, set)):
            tvl_val = tvl_val[0] if len(tvl_val) == 1 else 0
        volume_val = llama_data.get("volume24h", 0)
        if isinstance(volume_val, (list, tuple, set)):
            volume_val = volume_val[0] if len(volume_val) == 1 else 0
        tvl = format_number(tvl_val)
        volume = format_number(volume_val)
        with col1:
            metric_card("Total RWA TVL", tvl, None, help_text="Total value locked across all tracked RWA tokens")
        with col2:
            metric_card("Active Wallets", "N/A", None, help_text="Not available from DefiLlama")
        with col3:
            metric_card("24h Volume", volume, None, help_text="Total trading volume in the last 24 hours")
        st.subheader("TVL by Token")
        tokens = llama_data.get("tokens", [])
        if tokens:
            tvl_data = pd.DataFrame(tokens)
            name_col = None
            for candidate in ["symbol", "name", "token", "tokens"]:
                if candidate in tvl_data.columns:
                    name_col = candidate
                    break
            value_col = None
            for candidate in ["tvl", "value", "amount"]:
                if candidate in tvl_data.columns:
                    value_col = candidate
                    break
            if name_col and value_col:
                fig = px.pie(
                    tvl_data,
                    values=value_col,
                    names=name_col,
                    title="TVL Distribution ($)",
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"Token-level TVL breakdown not available: columns found {list(tvl_data.columns)}.")
        else:
            st.info("Token-level TVL breakdown not available from DefiLlama.")
    else:
        st.warning("No real-time TVL data available.")
    st.subheader("Recent Activity")
    st.markdown("[Data Source: Ondo Finance Twitter](https://twitter.com/ondo_finance) ")
    st.info("Recent activity can be fetched from social feeds or on-chain events. See [Ondo Twitter](https://twitter.com/ondo_finance) for latest updates.")

elif page == "Token Analysis":
    st.title(f"{selected_token} Token Analysis")
    st.markdown("[Data Source: CoinGecko](https://www.coingecko.com/) ")
    token_map = {"OUSG": "ousg", "USDY": "usdy", "OMMF": "ommf"}
    coingecko_id = token_map.get(selected_token, "ousg")
    try:
        price_url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/market_chart?vs_currency=usd&days={time_period_days}"
        price_resp = requests.get(price_url)
        price_data = price_resp.json() if price_resp.status_code == 200 else None
    except Exception as e:
        price_data = None
        st.error(f"Error fetching CoinGecko data: {e}")
    if price_data and "prices" in price_data:
        price_df = pd.DataFrame(price_data["prices"], columns=["timestamp", "price"])
        price_df["date"] = pd.to_datetime(price_df["timestamp"], unit="ms")
        col1, col2, col3 = st.columns(3)
        current_price = price_df["price"].iloc[-1]
        price_change = ((current_price / price_df["price"].iloc[0]) - 1) * 100
        with col1:
            metric_card("Current Price", f"${current_price:.4f}", round(price_change, 2))
        with col2:
            metric_card("Premium/Discount", "N/A", None, help_text="Premium or discount to the underlying asset")
        with col3:
            metric_card("30-Day Volatility", "N/A", None)
        st.subheader("Price History")
        fig = px.line(
            price_df,
            x="date",
            y="price",
            title=f"{selected_token} Price History"
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Price (USD)")
        st.plotly_chart(fig, use_container_width=True)
        if "total_volumes" in price_data:
            volume_df = pd.DataFrame(price_data["total_volumes"], columns=["timestamp", "volume"])
            volume_df["date"] = pd.to_datetime(volume_df["timestamp"], unit="ms")
            st.subheader("Trading Volume")
            fig = px.bar(
                volume_df,
                x="date",
                y="volume",
                title=f"{selected_token} Trading Volume"
            )
            fig.update_layout(xaxis_title="Date", yaxis_title="Volume (USD)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No real-time price data available.")

elif page == "Wallet Distribution":
    st.title(f"{selected_token} Wallet Distribution")
    st.markdown("[Data Source: Etherscan Token Holders](https://etherscan.io/token/tokenholderchart) ")
    etherscan_token_map = {
        "OUSG": "0x9d4643ecb8e6e3a0b6b6b6b6b6b6b6b6b6b6b6b6",  
        "USDY": "0x1234567890abcdef1234567890abcdef12345678",
        "OMMF": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
    }
    contract_address = etherscan_token_map.get(selected_token)
    etherscan_api_key = "YourEtherscanAPIKey"  
    if contract_address:
        try:
            holders_url = f"https://api.etherscan.io/api?module=token&action=tokenholderlist&contractaddress={contract_address}&page=1&offset=100&apikey={etherscan_api_key}"
            holders_resp = requests.get(holders_url)
            holders_data = holders_resp.json() if holders_resp.status_code == 200 else None
        except Exception as e:
            holders_data = None
            st.error(f"Error fetching Etherscan holders: {e}")
        if holders_data and holders_data.get("status") == "1":
            holders = holders_data.get("result", [])
            total_holders = len(holders)
            whale_wallets = sum(1 for h in holders if float(h.get("balance", 0)) > 0.01)
            retail_wallets = total_holders - whale_wallets
            col1, col2 = st.columns(2)
            with col1:
                metric_card("Total Holders", total_holders, None)
            with col2:
                metric_card("Whale Wallets", whale_wallets, None, help_text="Wallets holding >1% of supply")
            st.subheader("Wallets Table (Top 100)")
            st.dataframe(pd.DataFrame(holders))
        else:
            st.warning("No real-time wallet distribution data available.")
    else:
        st.warning("No contract address available for this token.")

elif page == "Bridge Activity":
    st.title(f"{selected_token} Bridge Activity")
    st.markdown("[Data Source: DefiLlama Bridged](https://defillama.com/bridged) ")
    try:
        bridge_url = "https://bridges.llama.fi/bridges"
        bridge_resp = requests.get(bridge_url)
        bridge_data = bridge_resp.json() if bridge_resp.status_code == 200 else None
    except Exception as e:
        bridge_data = None
        st.error(f"Error fetching DefiLlama bridge data: {e}")
    if bridge_data and "bridges" in bridge_data:
        bridges = bridge_data["bridges"]
        token_bridges = [b for b in bridges if selected_token.lower() in (b.get("symbol", "").lower() + b.get("name", "").lower())]
        if token_bridges:
            st.subheader(f"{selected_token} Bridge Summary")
            bridge_df = pd.DataFrame(token_bridges)
            cols = [c for c in ["name", "symbol", "category", "tvl", "chains", "url"] if c in bridge_df.columns]
            st.dataframe(bridge_df[cols])
        else:
            st.info(f"No bridge data found for {selected_token} on DefiLlama.")
    else:
        st.warning("No real-time bridge data available from DefiLlama.")
    st.info("Bridge activity data can also be fetched from open bridge APIs like Wormhole, LayerZero, or Axelar. See [Wormhole Docs](https://docs.wormhole.com/) for API details.")

elif page == "DeFi Usage":
    st.title(f"{selected_token} DeFi Usage")
    st.markdown("[Data Source: DefiLlama](https://defillama.com/) ")
    try:
        llama_url = f"https://api.llama.fi/protocol/ondo-finance"
        llama_resp = requests.get(llama_url)
        llama_data = llama_resp.json() if llama_resp.status_code == 200 else None
    except Exception as e:
        llama_data = None
        st.error(f"Error fetching DefiLlama data: {e}")
    if llama_data and "chains" in llama_data:
        chains = llama_data["chains"]
        if isinstance(chains, dict):
            defi_df = pd.DataFrame([{"protocol": k, "tvl": v} for k, v in chains.items()])
        elif isinstance(chains, list):
            defi_df = pd.DataFrame(chains)
            if not set(["protocol", "tvl"]).issubset(defi_df.columns):
                if "name" in defi_df.columns:
                    defi_df = defi_df.rename(columns={"name": "protocol"})
        else:
            defi_df = pd.DataFrame()
        st.subheader("TVL by Protocol")
        if not defi_df.empty and set(["protocol", "tvl"]).issubset(defi_df.columns):
            fig = px.pie(
                defi_df,
                values="tvl",
                names="protocol",
                title=f"{selected_token} TVL Distribution by Protocol",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            st.subheader("TVL by Protocol (USD)")
            fig = px.bar(
                defi_df,
                x="protocol",
                y="tvl",
                title=f"{selected_token} TVL by Protocol",
                color="protocol"
            )
            fig.update_layout(xaxis_title="Protocol", yaxis_title="TVL (USD)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No real-time DeFi usage data available or required columns missing.")
    else:
        st.warning("No real-time DeFi usage data available.")

elif page == "Competitor Analysis":
    st.title("RWA Competitor Analysis")
    st.markdown("[Data Source: DefiLlama](https://defillama.com/) ")
    try:
        protocols_url = "https://api.llama.fi/protocols"
        protocols_resp = requests.get(protocols_url)
        protocols_data = protocols_resp.json() if protocols_resp.status_code == 200 else None
    except Exception as e:
        protocols_data = None
        st.error(f"Error fetching DefiLlama protocols: {e}")
    if protocols_data:
        rwa_protocols = [p for p in protocols_data if any(t in p.get("category", "") for t in ["RWA", "Real World Asset"])]
        if rwa_protocols:
            market_share_df = pd.DataFrame([{ "issuer": p["name"], "tvl": p["tvl"] } for p in rwa_protocols])
            st.subheader("Market Share by TVL")
            fig = px.pie(
                market_share_df,
                values="tvl",
                names="issuer",
                title="RWA Market Share by TVL",
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            st.subheader("Issuer Comparison Table")
            market_share_df["TVL"] = market_share_df["tvl"].apply(format_number)
            st.table(market_share_df[["issuer", "TVL"]].rename(columns={"issuer": "Issuer"}))
        else:
            st.warning("No RWA protocols found in DefiLlama.")
    else:
        st.warning("No real-time competitor data available.")

elif page == "Market Maker Activity":
    st.title("Market Maker Activity")
    st.info("Fivetran Webhook: For automated data sync, POST to `/webhook/fivetran` on your FastAPI backend after each sync. Configure this in your Fivetran dashboard.")
    mm_data = {}
    import random
    random.seed(42)
    for mm_name in ["MM1", "MM2", "MM3"]:
        daily_data = []
        for date in pd.date_range(end=datetime.now(), periods=time_period_days, freq="D"):
            weekday = date.weekday()
            base_volume = 500000 if weekday < 5 else 300000
            daily_volume = max(100000, base_volume + random.randint(-150000, 200000))
            buy_percentage = random.uniform(0.4, 0.6)
            buy_volume = daily_volume * buy_percentage
            sell_volume = daily_volume * (1 - buy_percentage)
            daily_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "total_volume": round(daily_volume, 2),
                "buy_volume": round(buy_volume, 2),
                "sell_volume": round(sell_volume, 2),
                "trades": random.randint(50, 200)
            })
        mm_data[mm_name] = daily_data
    selected_mm = st.selectbox("Select Market Maker", list(mm_data.keys()))
    mm_df = pd.DataFrame(mm_data[selected_mm])
    total_volume = mm_df["total_volume"].sum()
    total_buy_volume = mm_df["buy_volume"].sum()
    total_sell_volume = mm_df["sell_volume"].sum()
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Total Volume", format_number(total_volume), None)
    with col2:
        metric_card("Buy Volume", format_number(total_buy_volume), None)
    with col3:
        metric_card("Sell Volume", format_number(total_sell_volume), None)
    st.subheader("Daily Trading Volume")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=mm_df["date"],
        y=mm_df["buy_volume"],
        name="Buy Volume",
        marker_color="green"
    ))
    fig.add_trace(go.Bar(
        x=mm_df["date"],
        y=mm_df["sell_volume"],
        name="Sell Volume",
        marker_color="red"
    ))
    fig.update_layout(
        title=f"{selected_mm} Daily Trading Volume",
        xaxis_title="Date",
        yaxis_title="Volume (USD)",
        barmode="stack"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Daily Trade Count")
    fig = px.line(
        mm_df,
        x="date",
        y="trades",
        title=f"{selected_mm} Daily Trade Count"
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Number of Trades")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Buy/Sell Ratio")
    mm_df["buy_ratio"] = mm_df["buy_volume"] / mm_df["total_volume"]
    fig = px.line(
        mm_df,
        x="date",
        y="buy_ratio",
        title=f"{selected_mm} Buy Ratio"
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Buy Ratio")
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Liquidity Provision")
    liquidity_data = {
        "MM1": {
            "total_liquidity": 12500000,
            "pools": [
                {"dex": "Curve", "pool": "OUSG/USDC", "liquidity": 5500000},
                {"dex": "Uniswap", "pool": "OUSG/ETH", "liquidity": 3500000},
                {"dex": "Curve", "pool": "USDY/USDC", "liquidity": 3500000}
            ]
        },
        "MM2": {
            "total_liquidity": 9800000,
            "pools": [
                {"dex": "Curve", "pool": "OUSG/USDC", "liquidity": 4200000},
                {"dex": "Uniswap", "pool": "USDY/ETH", "liquidity": 2800000},
                {"dex": "Curve", "pool": "USDY/USDC", "liquidity": 2800000}
            ]
        },
        "MM3": {
            "total_liquidity": 7500000,
            "pools": [
                {"dex": "Curve", "pool": "OUSG/USDC", "liquidity": 3000000},
                {"dex": "Uniswap", "pool": "OUSG/ETH", "liquidity": 2500000},
                {"dex": "Curve", "pool": "USDY/USDC", "liquidity": 2000000}
            ]
        }
    }
    st.info(f"Total Liquidity Provided: {format_number(liquidity_data[selected_mm]['total_liquidity'])}")
    liquidity_df = pd.DataFrame(liquidity_data[selected_mm]["pools"])
    fig = px.pie(
        liquidity_df,
        values="liquidity",
        names="pool",
        title=f"{selected_mm} Liquidity by Pool",
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Liquidity by Pool")
    liquidity_df["liquidity_formatted"] = liquidity_df["liquidity"].apply(format_number)
    st.table(liquidity_df[["dex", "pool", "liquidity_formatted"]].rename(
        columns={"dex": "DEX", "pool": "Pool", "liquidity_formatted": "Liquidity"}
    ))

st.sidebar.subheader("Download Data")
download_option = st.sidebar.selectbox(
    "Select Data to Download",
    ["Token Price History", "Wallet Distribution", "Bridge Activity", "DeFi Usage", "Market Maker Activity"],
    key="sidebar_download_option_select"
)

if st.sidebar.button("Download CSV"):
    st.sidebar.success(f"{download_option} data would be downloaded as CSV")

st.sidebar.markdown("---")
st.sidebar.info(
    "OnChain Pulse: Analytics Dashboard for Tokenized Assets. "  
    "Data is for demonstration purposes only."
)
