from threading import Thread
import time
import base64

import numpy as np
import pyautogui
import cv2

from server.server import SERVER

#nuitka --standalone --onefile --include-data-dir=templates=templates main.py

def main():
    SERVER.setup()
    SERVER.run()

if __name__ == "__main__":
    main()