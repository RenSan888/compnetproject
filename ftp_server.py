# ftp_server.py
import socket
import os
from packet import Packet

def save_file(sock, addr, filename):
    """Receive file data from a client and save to local disk."""
    print(f"Receiving file: {filename}")
    with open(filename, "wb") as f:
        expected_seq = 0  # Next expected sequence number
        while True:
            data, _ = sock.recvfrom(4096)
            try:
                packet = Packet.from_bytes(data)  # Parse received packet

                # Check if packet is the expected sequence
                if packet.seq_num == expected_seq:
                    if packet.flags == 0xFF:
                        # End-of-transfer packet detected
                        print("File transfer complete.")
                        break
                    # Write valid data to file
                    f.write(packet.payload)
                    expected_seq += 1

                # Send acknowledgment (even for duplicate packets)
                ack = Packet(0, packet.seq_num, 1)
                sock.sendto(ack.to_bytes(), addr)
            except Exception:
                # Ignore corrupted or incomplete packets
                continue

def send_file(sock, addr, filename):
    """Read a file and send it to a client using Go-Back-N."""
    from gbn_protocol import GBNProtocol

    # Ensure the requested file exists
    if not os.path.exists(filename):
        print("File not found.")
        return

    # Split file into 1 KB chunks
    with open(filename, "rb") as f:
        chunks = []
        while chunk := f.read(1024):
            chunks.append(chunk)

    # Initialize GBN and send data
    gbn = GBNProtocol(sock, addr)
    gbn.send_data(chunks)

def main():
    """Main server loop — waits for PUT/GET commands and handles them."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("localhost", 9000))
    print("Server listening on UDP port 9000...")

    while True:
        data, addr = sock.recvfrom(2048)

        try:
            # Try decoding only the very first few bytes as UTF-8 — command packets are short text
            command_text = data.decode(errors="ignore").strip()
            command = command_text.split()

            if not command:
                continue  # Ignore empty or undecodable data

            if command[0] == "PUT":
                sock.sendto(b"OK", addr)
                save_file(sock, addr, command[1])

            elif command[0] == "GET":
                sock.sendto(b"OK", addr)
                send_file(sock, addr, command[1])

        except UnicodeDecodeError:
            # Ignore any non-text packets (like binary file data)
            continue

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
