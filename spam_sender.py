import asyncio
import websockets


DEFAULT_END = 'ws://localhost:8765/channel1/'
MSG_COUNTER = 100
PATH_COUNTER = 10

async def send_message2():
    for i in range (0, PATH_COUNTER):
        connection_string = DEFAULT_END + str(i) + '/'
        async with websockets.connect(connection_string) as websocket:
            for j in range(0, MSG_COUNTER):
                message = 'Hello, World!' + str(j)
                await websocket.send(message)
                print(f"Sent message: {message} to channel {connection_string}")

async def send_message():

    async with websockets.connect(DEFAULT_END) as websocket:
        for j in range(0, MSG_COUNTER):
            message = str(j)
            await websocket.send(message)
            print(f"Sent message: {message}")

asyncio.get_event_loop().run_until_complete(send_message())