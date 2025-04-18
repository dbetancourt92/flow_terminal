import asyncio
import websockets

clients = set()

# ✅ MUST accept both websocket and path
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
        print(f"❌ Error in connection: {e}")
    finally:
        clients.remove(websocket)
        print(f"🔴 Disconnected: {websocket.remote_address}")

async def main():
    print("✅ WebSocket running on ws://127.0.0.1:8888")
    async with websockets.serve(handler, "127.0.0.1", 8888):  # No lambda, no partial
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
