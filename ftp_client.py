# ftp_client.py

# Import socket module for UDP communication
import socket

# Import os module for file system operations
import os

# Import Packet class and constants from packet.py
from packet import Packet, DATA, ACK, EOT

# Import GBNProtocol class to send files reliably
from gbn_protocol import GBNProtocol


def upload(sock, server_addr, filename):
    """Upload a file to the server using Go-Back-N protocol."""

    if not os.path.exists(filename):
        print("File not found.")
        return

    # Send PUT command to server with filename
    sock.sendto(f"PUT {filename}".encode(), server_addr)

    # Wait for server response
    resp, _ = sock.recvfrom(1024)
    if resp != b"OK":  # Server must approve the upload
        print("Server refused file upload.")
        return

    # Read the file in 1 KB chunks
    chunks = []
    with open(filename, "rb") as f:
        while chunk := f.read(1024):
            chunks.append(chunk)

    # Use Go-Back-N protocol to reliably send chunks
    gbn = GBNProtocol(sock, server_addr)
    gbn.send_data(chunks)
    print("Upload complete.")


def download(sock, server_addr, filename):
    """Download a file from the server using Go-Back-N protocol."""

    # Send GET command to server
    sock.sendto(f"GET {filename}".encode(), server_addr)

    # Wait for server response
    resp, _ = sock.recvfrom(1024)
    if resp != b"OK":  # Server must approve the download
        print("Server refused file download.")
        return

    expected_seq = 0  # Next expected sequence number
    sock.settimeout(3)  # Temporary timeout to detect stalled transfer

    # Open file in write-binary mode
    with open(filename, "wb") as f:
        while True:
            try:
                # Receive a UDP packet (up to 4096 bytes)
                data, _ = sock.recvfrom(4096)
            except socket.timeout:
                print("Server stopped sending. Download aborted.")
                break

            try:
                # Convert received bytes into a Packet object
                packet = Packet.from_bytes(data)

                if packet.seq_num == expected_seq:  # Only accept the expected packet
                    if packet.flags == EOT:  # End-of-Transmission packet
                        ack = Packet(0, packet.seq_num, ACK)
                        sock.sendto(ack.to_bytes(), server_addr)  # ACK EOT
                        print("Download complete.")
                        break

                    # Write valid data to file
                    f.write(packet.payload)
                    expected_seq += 1

                # Always ACK received packet (even duplicates)
                ack = Packet(0, packet.seq_num, ACK)
                sock.sendto(ack.to_bytes(), server_addr)

            except Exception:
                # Ignore invalid packets or checksum failures
                continue

    sock.settimeout(None)  # Reset socket to blocking mode after transfer


def main():
    # Create UDP socket for client
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Server address (localhost and UDP port 9000)
    server_addr = ("127.0.0.1", 9000)

    # Command loop for client
    while True:
        command = input("ftp> ").strip()  # Prompt user for command

        if command.startswith("PUT "):  # Upload file
            upload(sock, server_addr, command.split()[1])
        elif command.startswith("GET "):  # Download file
            download(sock, server_addr, command.split()[1])
        elif command in ("exit", "quit"):  # Exit client
            print("Goodbye")
            break


# Run the client if this script is executed directly
if __name__ == "__main__":
    main()


