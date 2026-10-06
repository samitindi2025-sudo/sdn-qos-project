import socket
import time

HOST = "0.0.0.0"
PORT = 5001

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

print(f"UDP server listening on port {PORT}")

while True:
    data, addr = server.recvfrom(2048)

    timestamp = time.time()

    print(
        f"Received {len(data)} bytes "
        f"from {addr[0]}:{addr[1]} "
        f"at {timestamp:.3f}"
    )
