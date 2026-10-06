import socket
import time

SERVER_IP = "10.0.0.2"
SERVER_PORT = 5001

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

message = b"HIGH_PRIORITY_TRAFFIC"

print(
    f"Sending UDP traffic to "
    f"{SERVER_IP}:{SERVER_PORT}"
)

for seq in range(1, 11):

    timestamp = time.time()

    packet = (
        f"{seq},{timestamp:.6f},".encode()
        + message
    )

    client.sendto(packet, (SERVER_IP, SERVER_PORT))

    print(
        f"Sent seq={seq} "
        f"timestamp={timestamp:.6f} "
        f"size={len(packet)}"
    )

    time.sleep(0.5)

client.close()
