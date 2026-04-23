import socketio
import psutil
import winreg
from core.common import CONFIG, Response, Request
from client.actions import ACTIONS

def load_server_url():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\cab-314", 0, winreg.KEY_READ) as key:
            url, _ = winreg.QueryValueEx(key, "ServerURL")
            return url
    except FileNotFoundError:
        return "http://127.0.0.1:5000"
    except Exception as e:
        print(f"Ошибка реестра: {e}")
        return "http://127.0.0.1:5000"

def load_client_ip(NETWORK_NAME):
    interfaces = psutil.net_if_addrs()
    for iface, address in interfaces.items():
        if NETWORK_NAME.lower() in iface.lower():
            for addr in address:
                if addr.family == 2:
                    return addr.address
    return "127.0.0.1"

ip = load_client_ip("Radmin")
url = load_server_url()

class Client():
    def __init__(self):
        self.socketio = socketio.Client(
            reconnection=True, 
            reconnection_attempts=0,
            reconnection_delay=2, 
            reconnection_delay_max=10,
            logger=True,
            engineio_logger=True
        )
    def send_response(self, resp: Response):
        self.socketio.emit("student_response", resp._asdict())
    def connect(self):
        self.socketio.connect(url, auth={"role": "student"})
    def setup_routes(self):
        @self.socketio.event
        def connect():
            print(f"connected succesfully to {url}")

        @self.socketio.on("execute_command")
        def on_command(data):
            request = Request(**data)
            ACTIONS.execute(self.send_response, request)
            
    def cleanup(self):
        self.socketio.disconnect()

CLIENT = Client()