import eventlet

eventlet.monkey_patch()  # <-- must come first

import time  # noqa: E402
from flask import Flask, request  # noqa: E402
from flask_socketio import SocketIO  # noqa: E402
import logging  # noqa: E402

logging.basicConfig(level=logging.INFO)


class ClientManager:
    NO_ACTIVITY_TIMEOUT = 60 * 60  # seconds

    def __init__(self):
        # {sid: last_activity_timestamp}
        self._clients = {}

    def update_activity(self, sid):
        self._clients[sid] = time.time()

    def remove_client(self, sid):
        self._clients.pop(sid, None)

    def get_idle_clients(self, timeout_seconds=NO_ACTIVITY_TIMEOUT):
        now = time.time()
        return [sid for sid, ts in self._clients.items() if now - ts > timeout_seconds]


def register_socket_io_handlers(socketio: SocketIO, clients: ClientManager):
    @socketio.on("connect")
    def handle_connect():
        sid = request.sid
        clients.update_activity(sid)

        logging.info(f"Client connected: {sid}")

    @socketio.on("message")
    def handle_message(msg):
        sid = request.sid
        clients.update_activity(sid)
        logging.info(f"Received from {sid}: {msg}")

        if msg == "process":
            socketio.start_background_task(target=process_task, sid=sid)

    def process_task(sid):
        for i in range(1, 11):
            socketio.emit("message", {"msg": f"Tick {i}"}, to=sid)
            eventlet.sleep(1)
        socketio.emit("message", {"msg": "done"}, to=sid)

    @socketio.on("disconnect")
    def handle_disconnect():
        sid = request.sid
        logging.info(f"Client disconnected: {sid}")
        clients.remove_client(sid)


def register_rest_endpoints(app):
    @app.route("/")
    def home():
        return "Server running."


# Background thread to enforce activity timeout
def check_idle_clients(clients: ClientManager, socketio: SocketIO):
    while True:
        for sid in clients.get_idle_clients():
            if sid in socketio.server.manager.get_participants("/", "/"):
                socketio.server.disconnect(sid)
                clients.remove_client(sid)
        eventlet.sleep(60)


if __name__ == "__main__":
    app = Flask(__name__)
    register_rest_endpoints(app=app)
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        ping_interval=25,  # server pings every 25s
        ping_timeout=60 * 10,  # disconnect if no pong in 60s
    )
    clients = ClientManager()
    register_socket_io_handlers(socketio=socketio, clients=clients)

    socketio.start_background_task(
        target=check_idle_clients, clients=clients, socketio=socketio
    )
    socketio.run(app, host="0.0.0.0", port=5002, debug=True)
