import asyncio
import websockets
import websockets.exceptions as wexcept

WS_PORT = 8765

server_connections = {}


async def handle_messages(path):
    """
    Defines a message handling method that continuously listens to incoming messages
    and passes them to appropriate connected clients.
    """
    while True:
        # Get message from async queue
        message = await queue.get()
        # If current path is in connection list
        if path in server_connections:
            # Get channel name and all it's connections
            conns = server_connections[path].copy()
            # For all connections for channel
            for conn in conns:
                try:
                    # Send message to all channel recipients
                    if conn != message['websocket']:
                        await conn.send(message['message'])
                # If connection closed then delete it from listeners list
                except websockets.exceptions.ConnectionClosedOK:
                    print('ERROR FROM HANDLER ClosedOK')
                    await websocket.close(code=1000, reason='')
                    server_connections[path].discard(conn)
                except websockets.exceptions.ConnectionClosedError:
                    print('ERROR FROM HANDLER ClosedError')
                    await websocket.close(code=1000, reason='')
                    server_connections[path].discard(conn)
        # Message processed and now we can end this task
        queue.task_done()

async def server(websocket, path):
    """
    This code defines an asynchronous server that listens to incoming WebSocket connections,
    receives incoming messages from clients, and sends received messages to other connected clients.
    """

    if path not in server_connections:
        server_connections[path] = set()
    server_connections[path].add(websocket)

    # Send message to all clients when new client is connected
    for conn in server_connections[path]:
        try:
            hello_text = '{"name": "", "fileId": "", "eventType": "mousePosition", "mouseX":0.0, "mouseY":0.0, "time": "2023-05-04T10:26:38.791913"}'
            await conn.send(hello_text)
        except websockets.exceptions.ConnectionClosedOK:
            print('ERROR FROM SERVER ClosedOk')
            await websocket.close(code=1000, reason='')
        except websockets.exceptions.ConnectionClosedError:
            print('ERROR FROM SERVER ClosedError')
            await websocket.close(code=1000, reason='')
        # await conn.send(f"{websocket.remote_address[0]} joined the channel.")

    try:
        async for message in websocket:
            # Debug message to console
            print(f'User {websocket.remote_address} sends message: {message} to {path}')

            send_to_current = False
            for conn in server_connections[path].copy():
                try:
                    if conn == websocket:
                        send_to_current = True
                        await conn.send(f"{message}")
                    else:
                        await conn.send(message)
                except websockets.exceptions.ConnectionClosedOK:
                    print('ERROR FROM SERVER ClosedOk')
                    await websocket.close(code=1000, reason='')
                    server_connections[path].discard(conn)
                except websockets.exceptions.ConnectionClosedError:
                    print('ERROR FROM SERVER ClosedError')
                    await websocket.close(code=1000, reason='')
                    server_connections[path].discard(conn)
                except Exception as e:
                    print('ERROR FROM SERVER UNHANDLED')
                    await websocket.close(code=1000, reason='')
                    server_connections[path].discard(conn)
            if send_to_current:
                message_data = {'websocket': websocket, 'message': f"{message}"}
                await queue.put(message_data)
    except websockets.exceptions.ConnectionClosedOK:
        print('ERROR FROM SERVER ClosedOk')
        await websocket.close(code=1000, reason='')
    except websockets.exceptions.ConnectionClosedError:
        print('ERROR FROM SERVER ClosedError')
        await websocket.close(code=1000, reason='')
    server_connections[path].discard(websocket)



async def main():
    """
    The main method launches the server and the message handling method, which are run concurrently.
    """
    # serve default ping_interval=20, ping_timeout=20, close_timeout=10,
    # Official docs https://websockets.readthedocs.io/en/stable/reference/asyncio/server.html#websockets.server.serve
    await asyncio.gather(
        websockets.serve(server, '0.0.0.0', WS_PORT),
        handle_messages('1')
    )

# If running as standalone application (not function side-import) as it should
if __name__ == '__main__':
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print('Keyboard Interrupted')
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
