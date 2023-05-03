import asyncio
import websockets

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
                    server_connections[path].discard(conn)
                except websockets.ConnectionClosedError:
                    server_connections[path].discard(conn)
        # Message processed and now we can end this task
        queue.task_done()


async def server(websocket, path):
    """
    This code defines an asynchronous server that listens to incoming WebSocket connections,
    receives incoming messages from clients, and sends received messages to other connected clients.
    """
    async for message in websocket:
        # Debug message to console
        print(f'User {websocket.remote_address} sends message: {message} to {path}')
        # If it new path (channel) then add it to our current set
        if path not in server_connections:
            server_connections[path] = set()
        server_connections[path].add(websocket)
        send_to_current = False
        # For each channel send received message
        for conn in server_connections[path].copy():
            try:
                # This resend message from sender to itself like "You: send something"
                if conn == websocket:
                    send_to_current = True
                    await conn.send(f"{message}")
                else:
                    await conn.send(message)
            except websockets.exceptions.ConnectionClosedOK:
                server_connections[path].discard(conn)
            except websockets.ConnectionClosedError:
                server_connections[path].discard(conn)
        if send_to_current:
            message_data = {'websocket': websocket, 'message': f"{message}"}
            await queue.put(message_data)
    # Delete connection when all messages were sent
    server_connections[path].discard(websocket)


async def main():
    """
    The main method launches the server and the message handling method, which are run concurrently.
    """
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
