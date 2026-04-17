import base64
import time
import threading
import ctypes
import os
import webbrowser
import winreg
import sys
import subprocess
from enum import Enum

import socketio
import cv2
import pyautogui
import psutil
import numpy as np

class WindowManager():
    class Modes(Enum):
        NONE = 0
        TEACHERS_STREAM = 1
        LOCK = 2
    def __init__(self):
        self.STREAM_WINDOW_NAME = "Teacher Screen"
        self.LOCK_WINDOW_NAME = "LOCK Screen"
        self.current_mode = self.Modes.NONE
        self.new_mode = self.Modes.NONE
        self.window_created = False
        self.current_frame = None 
    def visuals_loop(self):
        while True:
            if self.new_mode != self.current_mode:
                cv2.destroyAllWindows()
                cv2.waitKey(1) 
                self.current_mode = self.new_mode
                self.window_created = False 

            window_name = ""
            display_frame = np.zeros((720, 1280, 3))

            if self.current_mode == self.Modes.LOCK:
                window_name = self.LOCK_WINDOW_NAME
                display_frame = np.zeros((1440, 3440, 3), dtype=np.uint8)
                cv2.putText(display_frame, "SYSTEM LOCKED", (1000, 720), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 12)
            elif self.current_mode == self.Modes.TEACHERS_STREAM:
                window_name = self.STREAM_WINDOW_NAME
                display_frame = self.current_frame if self.current_frame is not None else np.zeros((720, 1280, 3), np.uint8)
            elif self.current_mode == self.Modes.NONE:
                time.sleep(0.1)
                continue

            if self.window_created and cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    self.window_created = False

            if not self.window_created:
                cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
                self.window_created = True

            cv2.imshow(window_name, display_frame)
            cv2.waitKey(1)
    def update_frame(self, frame):
        self.current_frame = frame
    def cleanup(self):
        cv2.destroyAllWindows()

class IpConfiguration():
    def load_server_url(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTER_PATH, 0, winreg.KEY_READ) as key:
                url, _ = winreg.QueryValueEx(key, "ServerURL")
                return url
        except FileNotFoundError:
            return "http://127.0.0.1:5000"
        except Exception as e:
            print(f"Ошибка реестра: {e}")
            return "http://127.0.0.1:5000"
    def load_client_ip(self):
        interfaces = psutil.net_if_addrs()
        for iface, address in interfaces.items():
            if self.NETWORK_NAME.lower() in iface.lower():
                for addr in address:
                    if addr.family == 2:
                        return addr.address
        return "127.0.0.1"
    def __init__(self, net_name, reg_path):
        self.NETWORK_NAME: str = net_name
        self.REGISTER_PATH = reg_path
        self.SERVER_URL = self.load_server_url()
        self.CLIENT_IP = self.load_client_ip()

class ActionRealisations():
    def __init__(self):
        self.ACTION_TO_FUNCTION = {
            "screenshot": self._screenshot,
            "lock": self._lock,
            "unlock": self._unlock,
            "message": self._message,
            "run_app": self._run_app,
            "kill_app": self._kill_app,
            "send_file": self._send_file,
            "collect_files": self._collect_files,
            "broadcast_start": self._broadcast_start,
            "broadcast_stop": self._broadcast_stop,
            "open_url": self._open_url,
            "show_console": self._show_console,
            "update": self._update,
            "shutdown": self._shutdown,
            "get_student_stream_start": self._get_student_stream_start,
            "get_student_stream_stop": self._get_student_stream_stop,
        }
    def _show_console(self, sender, action, args):
        UTILLITY.set_console_visibility(args["visibility"])
        NETWORK_MANAGER.send_response(sender, action, "200")
    
    def _screenshot(self, sender, action, args):
        screen = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
        b64_frame = base64.b64encode(buffer).decode("utf-8")
        NETWORK_MANAGER.send_response(sender, action, b64_frame)
    
    def _lock(self, sender, action, args):
        WINDOW_MANAGER.new_mode = WINDOW_MANAGER.Modes.LOCK
        NETWORK_MANAGER.send_response(sender, action, "200")
    
    def _unlock(self, sender, action, args):
        WINDOW_MANAGER.new_mode = WINDOW_MANAGER.Modes.NONE
        NETWORK_MANAGER.send_response(sender, action, "200")
    
    def _message(self, sender, action, args):
        ctypes.windll.user32.MessageBoxW(0, args["text"], args["title"], 0x00200000 | 0x00040000 | 0x00000040 | 0x00010000)
        NETWORK_MANAGER.send_response(sender, action, "200")
    
    def _run_app(self, sender, action, args):
        subprocess.Popen([args["path"]])
        NETWORK_MANAGER.send_response(sender, action, "200")
    
    def _kill_app(self, sender, action, args):
        os.system(f"taskkill /F /IM {args['process']}")
        NETWORK_MANAGER.send_response(sender, action, "200")
    
    def _send_file(self, sender, action, args):
        file_bytes = base64.b64decode(args.get("file_data"))
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        full_path = os.path.join(desktop_path, args.get("file_name"))
        with open(full_path, "wb") as f:
            f.write(file_bytes)
        NETWORK_MANAGER.send_response(sender, action, "200")
    
    def _collect_files(self, sender, action, args):
        NETWORK_MANAGER.send_response(sender, action, "200")
    
    def _broadcast_start(self, sender, action, args):
        WINDOW_MANAGER.new_mode = WINDOW_MANAGER.Modes.TEACHERS_STREAM
        NETWORK_MANAGER.send_response(sender, action, "200")
    
    def _broadcast_stop(self, sender, action, args):
        WINDOW_MANAGER.new_mode = WINDOW_MANAGER.Modes.NONE
        NETWORK_MANAGER.send_response(sender, action, "200")
    
    def _open_url(self, sender, action, args):
        url = args.get("url")
        webbrowser.open(url)
        NETWORK_MANAGER.send_response(sender, action, "200")

    def _update(self, sender, action, args):
        process = subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "iwr \"https://github.com/timbundon/cab-314/raw/refs/heads/main/client/install.ps1\" | iex"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )   
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            print("Команда успешно выполнена:")
            print(stdout)
            NETWORK_MANAGER.send_response(sender, action, "success")
        else:
            print(f"Ошибка при выполнении (код {process.returncode}):")
            print(stderr)
            NETWORK_MANAGER.send_response(sender, action, f"err: {process.returncode}")

    def _shutdown(self, sender, action, args):
        os.system("shutdown /s /f /t 1")
        NETWORK_MANAGER.send_response(sender, action, "shutdowned successfully")

    def _get_student_stream_start(self, sender, action, args):
        STREAM_MANAGER.subscribe(sender)
        NETWORK_MANAGER.send_response(sender, action, "subscribed")

    def _get_student_stream_stop(self, sender, action, args):
        STREAM_MANAGER.unsubscrite(sender)
        NETWORK_MANAGER.send_response(sender, action, "subscribed")

    def execute(self, sender, action, args):
        func = self.ACTION_TO_FUNCTION.get(action)
        if func:
            threading.Thread(target=func, args=(sender, action, args), daemon=True).start()
        else:
            NETWORK_MANAGER.send_response(sender, action, f"error: invalid action called {action}")
            print(f"error: invalid action {action}")

class NetworkManager():
    def __init__(self):
        self.socketio = socketio.Client(
            reconnection=True, 
            reconnection_attempts=0,
            reconnection_delay=2, 
            reconnection_delay_max=10,
            logger=True,
            engineio_logger=True
        )
    def send_response(self, sender, action, result):
        self.socketio.emit("client_response", {"sender": sender, "ip": IP_CONFIGURATION.CLIENT_IP, "action": action, "result": result})
    def send_stream_frame(self, listeners, b64_frame):
        self.socketio.emit("display_stream_frame", {"sid": self.socketio.sid, "ip": IP_CONFIGURATION.CLIENT_IP, "image": b64_frame, "listeners": list(listeners)})
    def connect(self):
        self.socketio.connect(IP_CONFIGURATION.SERVER_URL, auth={"role": "student"})
    def setup_routes(self):
        @self.socketio.event
        def connect():
            print(f"connected succesfully to {IP_CONFIGURATION.SERVER_URL}")

        @self.socketio.on('stream_frame')
        def on_frame(data):
            img_bytes = base64.b64decode(data['image'])
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                WINDOW_MANAGER.update_frame(frame)

        @self.socketio.on("execute_command")
        def on_command(data):
            action = data["action"]
            args = data.get("args", {})
            sender = data["sender"]
            ACTION_REALISATIONS.execute(sender, action, args)
    def cleanup(self):
        self.socketio.disconnect()

class Utillity():
    def __init__(self):
        pass
    def set_console_visibility(self, visiblity):
        SW_HIDE = 0
        SW_SHOW = 5
        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            if visiblity:
                ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                style &= ~WS_EX_TOOLWINDOW
                style |= WS_EX_APPWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            else:
                ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                style |= WS_EX_TOOLWINDOW
                style &= ~WS_EX_APPWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

class StreamManager():
    def __init__(self, fps):
        self.FPS = fps
        self.listeners = set()
    def worker(self):
        while True:
            try:
                if (len(self.listeners) > 0):
                    screen = pyautogui.screenshot()
                    frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
                    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    b64_frame = base64.b64encode(buffer).decode("utf-8")
                    NETWORK_MANAGER.send_stream_frame(self.listeners, b64_frame)
            except OSError:
                print("no screen")
            except Exception as e:
                print(f"err: {e}")
            time.sleep(1/self.FPS)
    def subscribe(self, sid):
        self.listeners.add(sid)
    def unsubscrite(self, sid):
        if sid in self.listeners:
            self.listeners.remove(sid)
    def start(self):
        threading.Thread(target=self.worker, daemon=True).start()

BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) or '__compiled__' in globals() else os.path.dirname(__file__)
IP_CONFIGURATION = IpConfiguration("Radmin", r"Software\cab-314")
WINDOW_MANAGER = WindowManager()
ACTION_REALISATIONS = ActionRealisations()
NETWORK_MANAGER = NetworkManager()
UTILLITY = Utillity()
STREAM_MANAGER = StreamManager(5)
STREAM_MANAGER.start()

def cleanup():
    WINDOW_MANAGER.cleanup()
    NETWORK_MANAGER.cleanup()

def main():
    UTILLITY.set_console_visibility(False)
    NETWORK_MANAGER.setup_routes()
    NETWORK_MANAGER.connect()
    WINDOW_MANAGER.visuals_loop()
    cleanup()

if __name__ == "__main__":
    main()