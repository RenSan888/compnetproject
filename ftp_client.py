# ftp_client.py
import socket
from packet import Packet
from gbn_protocol import GBNProtocol

def upload(sock, server_addr, filename):
    """Send a file to the server using the Go-Back-N protocol."""
    sock.sendto(f"PUT {filename}".encode(), server_addr)
    resp, _ = sock.recvfrom(1024)

    if resp != b"OK":
        print("Server refused file upload.")
        return

    # Read file and split into 1 KB chunks
    with open(filename, "rb") as f:
        chunks = []
        while chunk := f.read(1024):
            chunks.append(chunk)

    # Use Go-Back-N for reliable delivery
    gbn = GBNProtocol(sock, server_addr)
    gbn.send_data(chunks)
    print("Upload Complete.")

def download(sock, server_addr, filename):
    """Request a file from the server and save it locally."""
    sock.sendto(f"GET {filename}".encode(), server_addr)
    resp, _ = sock.recvfrom(1024)

    if resp != b"OK":
        print("Server refused file download.")
        return

    with open(filename, "wb") as f:
        expected_seq = 0  # Next expected packet sequence number
        while True:
            data, _ = sock.recvfrom(4096)
            try:
                packet = Packet.from_bytes(data)

                if packet.seq_num == expected_seq:
                    if packet.flags == 0xFF:
                        print("Download complete.")
                        break
                    f.write(packet.payload)
                    expected_seq += 1

                # Send acknowledgment regardless (supports retransmissions)
                ack = Packet(0, packet.seq_num, 1)
                sock.sendto(ack.to_bytes(), server_addr)
            except Exception:
                # Ignore corrupted packets
                continue

def main():
    """Interactive client interface."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("localhost", 9001))  # Client listens on port 9001
    server_addr = ("localhost", 9000)

    while True:
        command = input("ftp> ")

        if command.startswith("PUT "):
            upload(sock, server_addr, command.split()[1])
        elif command.startswith("GET "):
            download(sock, server_addr, command.split()[1])
        elif command in ("exit", "quit"):
            print("Goodbye")
            break

if __name__ == "__main__":
    main()
