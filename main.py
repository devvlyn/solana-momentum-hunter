import asyncio
import websockets
import json
import requests
import time
import os
from collections import defaultdict
from dotenv import load_dotenv

# 1. ENVIRONMENT SETUP
load_dotenv()
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
WSS_URL = f"wss://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
TELEGRAM_TOKEN = os.getenv("TOKEN_TELEGRAM")
CHAT_ID = os.getenv("CHAT_ID")

# 2. BOT CONFIGURATION
RAYDIUM_V4 = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
queue = asyncio.Queue()
watchlist = set()
history = defaultdict(list)  # {token: [(timestamp, is_buy, sol_vol, price)]}

# "Pressure Cooker" Parameters
MIN_BUY_RATIO = 0.75       # 75% buys minimum
MIN_TXS = 5
MAX_LATERALIZATION = 15.0  # Max price variation percentage
WORKER_DELAY = 0.6         # Seconds between RPC requests (Safe for Helius rate limits)

# 3. WATCHLIST MODULE (0 RPC Credits)
async def update_watchlist():
    global watchlist
    while True:
        try:
            url = "https://api.dexscreener.com/latest/dex/search?q=solana"
            res = requests.get(url, timeout=5).json()
            # Filter: MarketCap between $5k and $500k
            watchlist = {
                p['baseToken']['address']
                for p in res.get('pairs', [])
                if p.get('chainId') == 'solana' and 5000 <= float(p.get('marketCap', 0)) <= 500000
            }
            print(f"🔄 Watchlist updated: {len(watchlist)} tokens tracked.")
        except Exception as e:
            print(f"Error updating watchlist: {e}")
        await asyncio.sleep(60)

# 4. TRANSACTION PROCESSOR (Worker)
async def worker():
    while True:
        sig = await queue.get()
        try:
            # Query Helius RPC (getTransaction)
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [sig, {"encoding": "jsonParsed"}]
            }
            res = requests.post(RPC_URL, json=payload, timeout=5).json()
            
            if "result" not in res or not res["result"]:
                queue.task_done()
                continue
            
            meta = res["result"].get("meta", {})
            post_balances = meta.get("postTokenBalances", [])
            
            for bal in post_balances:
                mint = bal.get("mint")
                if mint in watchlist:
                    # Direction calculation logic (Simplified placeholder)
                    is_buy = True 
                    sol_vol = 0.5  # Volume placeholder
                    price = 0.001  # Price placeholder
                    
                    history[mint].append((time.time(), is_buy, sol_vol, price))
                    
                    # Analyze "Pressure Cooker" momentum
                    swaps = [s for s in history[mint] if time.time() - s[0] < 300]
                    if len(swaps) >= MIN_TXS:
                        buys = sum(1 for s in swaps if s[1])
                        ratio = buys / len(swaps)
                        if ratio >= MIN_BUY_RATIO:
                            # Trigger Alert
                            print(f"🔥 PRESSURE COOKER DETECTED: {mint} | Ratio: {ratio * 100:.1f}%")
                            # Telegram notification / Sniper execution logic here
            
        except Exception as e:
            print(f"Error processing transaction signature: {e}")
        
        await asyncio.sleep(WORKER_DELAY)
        queue.task_done()

# 5. WEBSOCKET EVENT LISTENER
async def listener():
    async with websockets.connect(WSS_URL) as ws:
        sub = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [{"mentions": [RAYDIUM_V4]}, {"commitment": "processed"}]
        }
        await ws.send(json.dumps(sub))
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if "params" in data:
                sig = data["params"]["result"]["value"]["signature"]
                await queue.put(sig)

# 6. APPLICATION ENTRY POINT
async def main():
    print("🚀 Master Solana Momentum Bot Started...")
    await asyncio.gather(
        update_watchlist(),
        listener(),
        worker(),
        worker()
    )

if __name__ == "__main__":
    asyncio.run(main())
