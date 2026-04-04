from threading import Thread, Event
import time
import base64
import os
import sys

from flask import Flask,  render_template, request
from flask_socketio import SocketIO, emit, join_room
import numpy as np
import pyautogui
import cv2

class ServerManager():
    def __init__(self, port):
        self.connections = {}
        self.PORT = port
    
    def get_clients(self):
        return list(self.connections.values())
    
    def pre_execution(self, target, action, args):
        if action == "broadcast_start":
            if target == "all":
                STREAM_MANAGER.listeners = self.get_clients()
            elif target not in STREAM_MANAGER.listeners:
                STREAM_MANAGER.listeners.append(target)
        elif action == "broadcast_stop":
            if target == "all":
                STREAM_MANAGER.listeners.clear()
            else:
                if target in STREAM_MANAGER.listeners:
                    STREAM_MANAGER.listeners.remove(target)
        elif action == "collect_files":
            if (not os.path.isdir(args["collection_name"])):
                os.mkdir(args["collection_name"])

    def setup_http_server(self):
        self.app = Flask(__name__, template_folder=os.path.join(BASE_PATH, "templates"))

        @self.app.route("/")
        def main():
            return render_template("index.html")

        @self.app.route("/clients")
        def clients():
            return self.get_clients()
        
    def setup_socket_server(self):
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        @self.socketio.on("connect")
        def handle_connect(auth):
            role = auth.get("role") if auth else "unknown"
            ip = request.remote_addr

            if role == "teacher":
                if (auth.get("token") != TOKEN):
                    return False
                join_room("teachers")
                print(f"teacher connected from {ip}")

            elif role == "student":
                join_room("students")
                join_room(ip)
                print(f"student connected from {ip}")
                self.connections[request.sid] = ip
                self.socketio.emit("update_clients", self.get_clients())

            else:
                return False

        @self.socketio.on("disconnect")
        def handle_disconnect():
            self.connections.pop(request.sid, None)
            self.socketio.emit("update_clients", self.get_clients())

        @self.socketio.on("send_command")
        def handle_command(data):
            target = data.get("target")
            self.pre_execution(target, data["action"], data["args"])
            if target == "all":
                emit("execute_command", data, to="students")
            else:
                emit("execute_command", data, to=target)

        @self.socketio.on("client_response")
        def handle_response(response_data):
            self.socketio.emit("display_result", response_data, to="teachers")

    def setup(self):
        self.setup_http_server()
        self.setup_socket_server()

    def send_stream_frame(self, listeners, b64_frame):
        for listener in listeners:
            self.socketio.emit("stream_frame", {"image": b64_frame}, to=listener)   

    def run(self):
        self.socketio.run(self.app, "0.0.0.0", self.PORT)

class StreamManager():
    def __init__(self, fps):
        self.FPS = fps
        self.listeners = []
    def stream_worker(self):
        while True:
            if len(self.listeners) > 0 and hasattr(SERVER_MANAGER, 'socketio'):
                screen = pyautogui.screenshot()
                frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                b64_frame = base64.b64encode(buffer).decode("utf-8")
                SERVER_MANAGER.send_stream_frame(self.listeners, b64_frame)
            time.sleep(1/self.FPS)
    def start(self):
        Thread(target=self.stream_worker, daemon=True).start()

TOKEN = base64.b64decode("cHIwZ3Jh").decode()
BASE_PATH = base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) or '__compiled__' in globals() else os.path.dirname(__file__)

SERVER_MANAGER = ServerManager(5000)
STREAM_MANAGER = StreamManager(30)

def main():
    SERVER_MANAGER.setup()
    STREAM_MANAGER.start()
    SERVER_MANAGER.run()

if __name__ == "__main__":
    main()