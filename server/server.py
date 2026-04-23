from flask import Flask,  render_template, request, redirect
from flask_socketio import SocketIO, emit, join_room

from core.common import Request, Response, CONFIG
import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

class Server():
    def __init__(self, port):
        self.connections = {}
        self.logs = []
        self.PORT = port

    def setup_http_server(self):
        self.app = Flask(__name__, template_folder=os.path.join(BASE_PATH, "templates"))

        @self.app.route("/")
        def main():
            return render_template("index.html")

        @self.app.route("/clients")
        def clients():
            return self.connections
        
    def setup_socket_server(self):
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        @self.socketio.on("connect")
        def handle_connect(auth):
            role = auth.get("role") if auth else "unknown"
            ip = request.remote_addr
            if role == "teacher":
                if (auth.get("token") != CONFIG.TOKEN):
                    return False
                join_room("teachers")
                print(f"teacher connected from {ip}")
            elif role == "student":
                join_room("students")
                print(f"student connected from {ip}")
                self.connections[request.sid] = ip
                self.socketio.emit("update_clients", self.connections)
            else:
                return False

        @self.socketio.on("disconnect")
        def handle_disconnect():
            self.connections.pop(request.sid, None)
            self.socketio.emit("update_clients", self.connections)

        @self.socketio.on("teacher_request")
        def handle_command(request_data):
            request = Request(**request_data)
            print(*request)
            if request.target == "all":
                emit("execute_command", request._asdict(), to="students")
            else:
                emit("execute_command", request._asdict(), to=request.target)

        @self.socketio.on("student_response")
        def handle_response(response_data):
            response = Response(**response_data)
            self.socketio.emit("display_result", response._asdict(), to=response.destination)

    def setup(self):
        self.setup_http_server()
        self.setup_socket_server() 

    def run(self):
        self.socketio.run(self.app, "0.0.0.0", self.PORT)

SERVER = Server(CONFIG.PORT)