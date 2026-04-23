import pyautogui
import cv2
import base64
import time
from threading import Thread

class StreamManager():
    def __init__(self, fps):
        self.FPS = fps
        self.listeners = []
    def stream_worker(self):
        while True:
            try:
                if len(self.listeners) > 0 and hasattr(SERVER_MANAGER, 'socketio'):
                    screen = pyautogui.screenshot()
                    frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
                    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    b64_frame = base64.b64encode(buffer).decode("utf-8")
                    SERVER_MANAGER.send_stream_frame(self.listeners, b64_frame)
            except OSError:
                print("no screen")
            except Exception as e:
                print(f"error: {e}")
            time.sleep(1/self.FPS)
    def start(self):
        Thread(target=self.stream_worker, daemon=True).start()