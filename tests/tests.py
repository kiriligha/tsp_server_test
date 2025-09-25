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
    sock.connect(('0.0.0.0', port))
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

def test_get_nonexistent(server):
    assert send_command('GET', 'nonexistent') == '$-1\r\n'

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

def test_empty_key_value(server):
    assert send_command('SET', '', '') == '-ERR cannot create a pair with empty objects\r\n'
    assert send_command('GET', '') == '$-1\r\n'

def test_large_value(server):
    large_value = 'a' * 1000
    assert send_command('SET', 'large', large_value) == '+OK\r\n'
    response = send_command('GET', 'large')
    assert response.startswith('$1000\r\n') and response.endswith('\r\n')

def test_del(server):
    assert send_command('SET', 'key', 'value') == '+OK\r\n'
    assert send_command('DEL', 'key') == '+OK\r\n'
    assert send_command('GET', 'key') == '$-1\r\n'
    assert send_command('DEL', 'nothing') == '-ERR there is no such key for DEL\r\n' 
    assert send_command('DEL') == '-ERR wrong number of arguments for DEL\r\n'