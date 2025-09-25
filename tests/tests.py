import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pytest
import time
from server.server import CacheServer 
import threading
import socket

@pytest.fixture(scope="module")
def server():
    s = CacheServer(port=6380)
    thread = threading.Thread(target=s.start)
    thread.daemon = True
    thread.start()
    yield s
    s.stop()

def send_command(*args, port=6380):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', port))
    command = b'*' + str(len(args)).encode() + b'\r\n'
    for arg in args:
        command += b'$' + str(len(arg)).encode() + b'\r\n' + arg.encode() + b'\r\n'
    sock.sendall(command)
    response = sock.recv(1024).decode()
    sock.close()
    return response

def test_set_get(server):
    assert send_command('SET', 'test', 'value') == '+OK\r\n'
    assert send_command('GET', 'test') == '$5\r\nvalue\r\n'

def test_get_nothing(server):
    assert send_command('GET', 'nothing') == '$-1\r\n'

def test_set_with_ttl(server):
    assert send_command('SET', 'ttl_key', 'ttl_value', 'EX', '1') == '+OK\r\n'
    assert send_command('GET', 'ttl_key') == '$9\r\nttl_value\r\n'
    time.sleep(1.5)
    assert send_command('GET', 'ttl_key') == '$-1\r\n'

def test_invalid_command(server):
    assert send_command('INVALID') == '-ERR unknown command\r\n'

def test_wrong_args_set(server):
    assert send_command('SET', 'key') == '-ERR wrong number of arguments for SET\r\n'

def test_wrong_args_get(server):
    assert send_command('GET') == '-ERR wrong number of arguments for GET\r\n'

def test_invalid_ttl(server):
    assert send_command('SET', 'key', 'value', 'EX', 'abc') == '-ERR invalid expire time\r\n'