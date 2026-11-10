# solana-momentum-hunter
Asynchronous Solana real-time momentum bot built in Python


# Solana Real-Time On-Chain Momentum Bot ("Pressure Cooker")

An asynchronous monitoring system built in Python to track low-cap token liquidity and detect high-momentum buying pressure on the Solana blockchain.

## System Architecture

The application handles high-frequency event streaming without blocking execution or reaching RPC rate limits. It decouples network listening from data processing using an asynchronous pipeline:

1. WebSocket Event Listener (`listener`): Connects directly to Helius RPC via WebSockets, subscribing to real-time transaction logs (`logsSubscribe`) targeting the Raydium V4 liquidity pool program (`675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8`).
2. Concurrent Queue (`asyncio.Queue`): Incoming transaction signatures are pushed instantly into an asynchronous queue to prevent backpressure or dropped messages.
3. Worker Pool (`worker`): Concurrent workers pull signatures from the queue, fetch transaction payloads via JSON-RPC (`getTransaction`), and evaluate token metrics against custom criteria.
4. Dynamic Watchlist (`update_watchlist`): Periodically polls public aggregators (DexScreener API) to filter active Solana tokens within a specific market capitalization range ($5k to $500k) without consuming RPC credits.

## Key Features

- Asynchronous Event Pipeline: Built using Python's `asyncio` and `websockets` libraries to maintain non-blocking, low-latency execution.
- Rate Limiting: Incorporates controlled worker delays (`WORKER_DELAY`) to respect RPC provider thresholds.
- Momentum Detection: Evaluates rolling windows of transaction frequency and buy-to-sell ratios (`MIN_BUY_RATIO = 0.75`) to identify accumulation spikes.
- Modular Structure: Clear division between environment setup, watchlist updates, queue management, and transaction evaluation.

## Tech Stack

- Language: Python 3.10+
- Concurrency & Async: `asyncio`, `collections.defaultdict`
- Networking & WebSockets: `websockets`, `requests`
- APIs & Nodes: Helius Solana RPC (WebSockets & JSON-RPC), DexScreener API
- Environment Management: `python-dotenv`

## Configuration and Setup

### 1. Prerequisites
Clone the repository and install the dependencies:

```bash
git clone [https://github.com/devvlyn/solana-momentum-hunter.git](https://github.com/devvlyn/solana-momentum-hunter.git
cd solana-momentum-hunter
pip install websockets requests python-dotenv
