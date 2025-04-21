import asyncio
import websockets

clients = set()

async def handler(websocket, path):  # ✅ FIXED: includes path
    clients.add(websocket)
    print(f"🟢 Connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"⬅️ Received: {message}")
            for client in clients:
                if client != websocket:
                    await client.send(message)
    except Exception as e:
        print(f"❌ Error in connection: {e}")
    finally:
        clients.remove(websocket)
        print(f"🔴 Disconnected: {websocket.remote_address}")

async def main():
    import os
    PORT = int(os.environ.get("PORT", 8888))
    print(f"✅ WebSocket running on ws://0.0.0.0:{PORT}")
    async with websockets.serve(handler, "0.0.0.0", PORT):  # ✅ FIXED
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
