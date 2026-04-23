from client.client import CLIENT

def main():
    CLIENT.setup_routes()
    CLIENT.connect()
    CLIENT.socketio.wait()
if __name__ == "__main__":
    main()