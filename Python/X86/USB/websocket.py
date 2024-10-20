import asyncio
from websockets.server import serve
async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)

async def main():
    async with serve(echo, "192.168.8.70", 8765):
        await asyncio.Future()  # run forever

asyncio.run(main())