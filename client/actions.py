from core.common import Request, Response, toogle_console
from threading import Thread
import os, base64, webbrowser
import cv2
import pyautogui
import ctypes
import subprocess

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
    def _show_console(self, callback, request: Request):
        toogle_console(request.args["visibility"])
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)
    
    def _screenshot(self, callback, request: Request):
        screen = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
        b64_frame = base64.b64encode(buffer).decode("utf-8")
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)
    
    def _lock(self, callback, request: Request):
        WINDOW_MANAGER.new_mode = WINDOW_MANAGER.Modes.LOCK
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)
    
    def _unlock(self, callback, request: Request):
        WINDOW_MANAGER.new_mode = WINDOW_MANAGER.Modes.NONE
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)
    
    def _message(self, callback, request: Request):
        ctypes.windll.user32.MessageBoxW(0, request.args["text"], request.args["title"], 0x00200000 | 0x00040000 | 0x00000040 | 0x00010000)
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)
    
    def _run_app(self, callback, request: Request):
        subprocess.Popen([request.args["path"]])
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)
    
    def _kill_app(self, callback, request: Request):
        os.system(f"taskkill /F /IM {request.args['process']}")
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)
    
    def _send_file(self, callback, request: Request):
        file_bytes = base64.b64decode(request.args.get("file_data"))
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        full_path = os.path.join(desktop_path, request.args.get("file_name"))
        with open(full_path, "wb") as f:
            f.write(file_bytes)
            response = Response(request.task_id, request.sender, "200", "200")
        callback(response)
    
    def _collect_files(self, callback, request: Request):
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)
    
    def _broadcast_start(self, callback, request: Request):
        WINDOW_MANAGER.new_mode = WINDOW_MANAGER.Modes.TEACHERS_STREAM
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)
    
    def _broadcast_stop(self, callback, request: Request):
        WINDOW_MANAGER.new_mode = WINDOW_MANAGER.Modes.NONE
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)
    
    def _open_url(self, callback, request: Request):
        url = request.args.get("url")
        webbrowser.open(url)
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)

    def _update(self, callback, request: Request):
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
            response = Response(request.task_id, request.sender, "200", "200")
            callback(response)
        else:
            print(f"Ошибка при выполнении (код {process.returncode}):")
            print(stderr)
            response = Response(request.task_id, request.sender, "200", "200")
            callback(response)

    def _shutdown(self, callback, request: Request):
        os.system("shutdown /s /f /t 1")
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)

    def _get_student_stream_start(self, callback, request: Request):
        STREAM_MANAGER.subscribe(sender)
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)

    def _get_student_stream_stop(self, callback, request: Request):
        STREAM_MANAGER.unsubscrite(sender)
        response = Response(request.task_id, request.sender, "200", "200")
        callback(response)

    def execute(self, callback, request: Request):
        func = self.ACTION_TO_FUNCTION.get(request.action)
        if func:
            Thread(target=func, args=(callback, request, ), daemon=True).start()
        else:
            response = Response(request.task_id, request.sender, "200", "200")
            callback(response)
            print(f"error: invalid action {request.action}")

ACTIONS = ActionRealisations()