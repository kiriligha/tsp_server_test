import socket
import threading

class CacheServer:
    def __init__(self, host: str = '127.0.0.1', port: int = 6379):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = True

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Сервер запущен по адресу {self.host}:{self.port}")
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except OSError:
                break

    def stop(self):
        self.running = False
        self.server_socket.close()

    def handle_client(self, client_socket: socket.socket):
        while self.running:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                client_socket.sendall(data.upper()) 
            except ConnectionResetError:
                break
        client_socket.close()

if __name__ == "__main__":
    server = CacheServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()