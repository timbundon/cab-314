from flask import Flask,  render_template, request, redirect
from flask_socketio import SocketIO, emit, join_room

from bus import BUS
import os

class NetworkManager:
    def start_http(self):
        app = Flask(__name__, template_folder=os.path.join(BASE_PATH, "templates"))

        @app.route("/")
        def root():
            render_template("index.html")
        
        @app.route("/connections")
        def connections():
            return self.connections
    def __init__(self, port):
        self.connections = {}
        self.port = port
