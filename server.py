import socket
import threading
import time
from typing import Dict

class CacheServer:
    def __init__(self, host: str = '127.0.0.1', port: int = 6379):
        self.host = host
        self.port = port
        self.cache: Dict[str, str] = {}
        self.ttl: Dict[str, float] = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")
        self.cleanup_thread.start()
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_socket,)).start()
            except OSError:
                break

    def stop(self):
        self.running = False
        self.server_socket.close()

    def _handle_client(self, client_socket: socket.socket):
        buffer = b''
        while self.running:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                buffer += data
                while buffer:
                    resp, consumed = self._parse_resp(buffer)
                    if resp is None:
                        break
                    buffer = buffer[consumed:]
                    response = self._process_command(resp)
                    client_socket.sendall(response)
            except ConnectionResetError:
                break
        client_socket.close()

    def _parse_resp(self, data: bytes) -> tuple:
        if not data.startswith(b'*'):
            return None, 0
        try:
            parts = data.split(b'\r\n')
            array_len = int(parts[0][1:].decode())
            expected_parts = 1 + array_len * 2
            if len(parts) < expected_parts:
                return None, 0
            command = []
            index = 1
            for _ in range(array_len):
                bulk_len = int(parts[index][1:].decode())
                index += 1
                value = parts[index].decode()
                if len(value) != bulk_len:
                    raise ValueError("Invalid bulk length")
                command.append(value)
                index += 1
            consumed = sum(len(p) + 2 for p in parts[:index])
            return command, consumed
        except Exception:
            return b"-ERR invalid command\r\n", len(data)

    def _process_command(self, command: list) -> bytes:
        if not command:
            return b"-ERR empty command\r\n"
        cmd = command[0].upper()
        handlers = {
            'GET': self._handle_get,
            'SET': self._handle_set,
        }
        handler = handlers.get(cmd)
        if handler:
            return handler(command)
        return b"-ERR unknown command\r\n"

    def _handle_get(self, command: list) -> bytes:
        if len(command) != 2:
            return b"-ERR wrong number of arguments for GET\r\n"
        key = command[1]
        self._expire_if_needed(key)
        value = self.cache.get(key)
        if value is None:
            return b"$-1\r\n"
        return b"$" + str(len(value)).encode() + b"\r\n" + value.encode() + b"\r\n"

    def _handle_set(self, command: list) -> bytes:
        if len(command) < 3:
            return b"-ERR wrong number of arguments for SET\r\n"
        key, value = command[1], command[2]
        ttl = None
        if len(command) > 3 and command[3].upper() == 'EX':
            if len(command) != 5:
                return b"-ERR syntax error for EX\r\n"
            try:
                ttl = int(command[4])
            except ValueError:
                return b"-ERR invalid expire time\r\n"
        self.cache[key] = value
        if ttl:
            self.ttl[key] = time.time() + ttl
        else:
            self.ttl.pop(key, None)
        return b"+OK\r\n"

    def _expire_if_needed(self, key: str):
        expire_time = self.ttl.get(key)
        if expire_time and time.time() > expire_time:
            self.cache.pop(key, None)
            self.ttl.pop(key, None)

    def _cleanup_expired(self):
        while self.running:
            keys_to_expire = [k for k, t in list(self.ttl.items()) if time.time() > t]
            for key in keys_to_expire:
                self.cache.pop(key, None)
                self.ttl.pop(key, None)
            time.sleep(1)

if __name__ == "__main__":
    server = CacheServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()