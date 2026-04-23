import ctypes
import logging
import base64
from typing import NamedTuple

class Config:
    def __init__(self):
        self.PORT = 5000
        self.TOKEN = base64.b64decode("cHIwZ3Jh").decode()

class EventBus:
    def __init__(self):
        self.listeners = {}
    def subscribe(self, event_name, callback):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)
    def emit(self, event_name, *args, **kwargs):
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                callback(*args, **kwargs)

class Request(NamedTuple):
    task_id: str
    target: str
    sender: str
    action: str
    args: dict[str, any]
    sent_at: str

class Response(NamedTuple):
    task_id: str
    destination: str
    status: str
    result: str

def configure_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def toogle_console(visiblity):
    SW_HIDE = 0
    SW_SHOW = 5
    GWL_EXSTYLE = -20
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_APPWINDOW = 0x00040000
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW if visiblity else SW_HIDE)
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style &= ~WS_EX_TOOLWINDOW
        style |= WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

BUS = EventBus()
CONFIG = Config()