import asyncio
import websockets

WS_PORT = 8765

server_connections = {}


async def handle_messages(path):
    while True:
        message = await queue.get()
        if path in server_connections:
            conns = server_connections[path].copy()
            for conn in conns:
                try:
                    if conn != message['websocket']:
                        await conn.send(message['message'])
                except websockets.exceptions.ConnectionClosedOK:
                    server_connections[path].discard(conn)
                except websockets.ConnectionClosedError:
                    server_connections[path].discard(conn)
        queue.task_done()


async def server(websocket, path):
    async for message in websocket:
        print(f'User {websocket.remote_address} sends message: {message} to {path}')
        if path not in server_connections:
            server_connections[path] = set()
        server_connections[path].add(websocket)
        send_to_current = False
        for conn in server_connections[path].copy():
            try:
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
    server_connections[path].discard(websocket)


async def main():
    await asyncio.gather(
        websockets.serve(server, '0.0.0.0', WS_PORT),
        handle_messages('1')
    )

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
