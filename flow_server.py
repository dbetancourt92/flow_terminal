import asyncio
import websockets
import os

clients = set()

# Handler for incoming websocket connections
async def handler(websocket, path):
    clients.add(websocket)
    print(f"🟢 Connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"⬅️ Received: {message}")
            to_remove = set()
            for client in clients:
                if client != websocket:
                    try:
                        await client.send(message)
                    except Exception as e:
                        print(f"⚠️ Failed to send to client: {e}")
                        to_remove.add(client)
            clients.difference_update(to_remove)
    except Exception as e:
        print(f"❌ Connection error: {e}")
    finally:
        clients.remove(websocket)
        print(f"🔴 Disconnected: {websocket.remote_address}")

# Main server start logic
async def main():
    port = int(os.environ.get("PORT", 8888))  # Render will set PORT
    print(f"✅ WebSocket server starting on ws://0.0.0.0:{port}")
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()  # Keep running

if __name__ == "__main__":
    asyncio.run(main())
