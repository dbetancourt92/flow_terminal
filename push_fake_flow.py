import asyncio
import websockets
import json
from datetime import datetime
import random

# 🔁 This will loop and push new flow data continuously
async def send_fake_flow():
    uri = "wss://flow-terminal.onrender.com"

    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to WebSocket server!")

            while True:
                row = generate_fake_row()
                try:
                    await websocket.send(json.dumps(row))
                    print("✅ Sent:", row)
                except Exception as e:
                    print("❌ Failed to send row:", row)
                    print("🚨 Error:", e)
                await asyncio.sleep(2)  # Delay between pushes

    except Exception as e:
        print("❌ Could not connect to WebSocket server")
        print("🚨 Error:", e)

# 🧪 Generate dummy options flow data
def generate_fake_row():
    tickers = ["AAPL", "TSLA", "SPY", "NVDA", "AMD"]
    sides = ["ASK", "BID", "MID"]
    types = ["CALL", "PUT"]

    return [
        datetime.now().strftime("%H:%M:%S"),                       # Time
        random.choice(tickers),                                   # Ticker
        random.choice(sides),                                     # Side
        str(random.randint(100, 500)),                             # Strike
        opt_type := random.choice(types),                          # Type
        "04/26/2025",                                              # Expiry
        str(random.randint(1, 90)),                                # DTE
        "$" + str(round(random.uniform(90, 500), 2)),              # Stock
        "$1.25 - $1.40",                                           # Bid-Ask
        "$" + str(round(random.uniform(0.5, 5.0), 2)),             # Spot
        str(random.randint(10, 500)),                              # Size
        f"${random.randint(10, 1000)}K",                           # Premium
        str(random.randint(100, 5000)),                            # Volume
        str(random.randint(100, 10000)),                           # OI
        f"{random.randint(10, 100)}%",                             # Chain %
        str(random.choice(["True", "False"])),                     # Multileg
    ]

# 🔁 Run the script
if __name__ == "__main__":
    asyncio.run(send_fake_flow())
