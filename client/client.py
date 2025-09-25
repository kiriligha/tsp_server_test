import socket

def send_command(*args, host='0.0.0.0', port=6379):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    command = b'*' + str(len(args)).encode() + b'\r\n'
    for arg in args:
        command += b'$' + str(len(arg)).encode() + b'\r\n' + arg.encode() + b'\r\n'
    sock.sendall(command)
    response = sock.recv(1024).decode()
    sock.close()
    return response

if __name__ == "__main__":
    print(send_command('SET', 'key', 'value'))
    print(send_command('GET', 'key'))
    print(send_command('DEL', 'key'))
    print(send_command('GET', 'key'))
    print(send_command('SET', 'key2', 'value2', 'EX', '5'))