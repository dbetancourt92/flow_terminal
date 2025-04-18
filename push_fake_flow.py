import asyncio
import websockets
import json
from datetime import datetime, timedelta
import random

def generate_fake_flow_batch(n=20):
    tickers = ["AAPL", "TSLA", "NVDA", "SPY", "QQQ"]
    sides = ["BID", "ASK"]
    types = ["CALL", "PUT"]
    now = datetime.now()
    flow_batch = []

    for _ in range(n):
        t = random.choice(tickers)
        s = random.choice(sides)
        otype = random.choice(types)
        row = {
            "time": (now - timedelta(seconds=random.randint(0, 3600))).strftime("%m/%d %H:%M:%S"),
            "ticker": t,
            "side": s,
            "strike": str(random.randint(100, 500)),
            "type": otype,
            "expiry": "04/25/2025",
            "dte": str(random.randint(1, 90)),
            "stock": "$" + str(round(random.uniform(90, 500), 2)),
            "bidask": "$1.20 - $1.30",
            "spot": "$" + str(round(random.uniform(1, 10), 2)),
            "size": str(random.randint(1, 30)),
            "premium": f"${random.randint(20, 500)}K",
            "volume": str(random.randint(100, 10000)),
            "oi": str(random.randint(100, 20000)),
            "chain_pct": f"{random.randint(30, 100)}%",
            "multi": random.choice(["True", "False"]),
            "sentiment": "Bullish" if otype == "CALL" else "Bearish"
        }
        flow_batch.append(row)
    return flow_batch

async def send_fake_flow():
    uri = "ws://127.0.0.1:8888"
    async with websockets.connect(uri) as websocket:
        await asyncio.sleep(1)
        while True:
            flow_batch = generate_fake_flow_batch()
            for row in flow_batch:
                await websocket.send(json.dumps(row))
                await asyncio.sleep(0.2)

asyncio.run(send_fake_flow())