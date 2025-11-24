# ftp_server.py

# Import socket module to handle UDP communication
import socket

# Import os module for file system operations
import os

# Import time module to handle timeouts and timestamps
import time

# Import Packet class and constants from packet.py
from packet import Packet, DATA, ACK, EOT

# Import GBNProtocol class for sending files reliably
from gbn_protocol import GBNProtocol


def save_file(sock, addr, filename):
    """Receive a file from the client using Go-Back-N protocol."""
    print(f"Receiving file: {filename}")

    expected_seq = 0  # Sequence number expected next
    last_packet_time = time.time()  # Timestamp of the last received packet

    sock.settimeout(1)  # Set a temporary socket timeout to detect stalled transfers

    # Open file in write-binary mode
    with open(filename, "wb") as f:
        while True:
            try:
                # Receive a UDP packet (up to 4096 bytes)
                data, _ = sock.recvfrom(4096)
            except socket.timeout:
                # If no packet received for 5 seconds, abort transfer
                if time.time() - last_packet_time > 5:
                    print("Client stopped sending. Transfer aborted.")
                    break
                else:
                    continue

            last_packet_time = time.time()  # Update last packet timestamp

            try:
                # Convert received bytes into a Packet object
                packet = Packet.from_bytes(data)

                if packet.seq_num == expected_seq:  # Only accept the expected sequence
                    if packet.flags == EOT:
                        # If End-of-Transmission packet received, send ACK and finish
                        ack = Packet(0, packet.seq_num, ACK)
                        sock.sendto(ack.to_bytes(), addr)
                        print("File transfer complete.")
                        break

                    # Write payload of valid data packet to file
                    f.write(packet.payload)
                    expected_seq += 1  # Expect next sequence number

                # Always send ACK, even for duplicates
                ack = Packet(0, packet.seq_num, ACK)
                sock.sendto(ack.to_bytes(), addr)

            except Exception:
                # Ignore invalid packets or checksum failures
                continue

    sock.settimeout(None)  # Reset socket to blocking mode after transfer


def send_file(sock, addr, filename):
    """Send a file to a client using Go-Back-N protocol."""
    if not os.path.exists(filename):
        print("File not found.")
        return

    # Read the file in 1 KB chunks
    chunks = []
    with open(filename, "rb") as f:
        while chunk := f.read(1024):
            chunks.append(chunk)

    # Initialize GBNProtocol with the socket and client address
    gbn = GBNProtocol(sock, addr)

    # Send all chunks reliably
    gbn.send_data(chunks)


def main():
    """Main server loop: waits for PUT/GET commands from clients."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket
    sock.bind(("127.0.0.1", 9000))  # Bind to localhost:9000
    print("Server listening on UDP port 9000...")

    while True:
        try:
            # Wait for incoming command (blocking)
            data, addr = sock.recvfrom(2048)

            # Decode command to string, ignoring errors
            command_text = data.decode(errors="ignore").strip()
            command = command_text.split()  # Split command into words

            if not command:  # Skip empty commands
                continue

            if command[0] == "PUT":
                # Client wants to upload a file
                if len(command) < 2:
                    sock.sendto(b"ERR Missing filename", addr)
                    continue

                sock.sendto(b"OK", addr)  # Acknowledge command
                save_file(sock, addr, command[1])  # Receive file
                print("Ready for next command...")

            elif command[0] == "GET":
                # Client wants to download a file
                if len(command) < 2:
                    sock.sendto(b"ERR Missing filename", addr)
                    continue

                sock.sendto(b"OK", addr)  # Acknowledge command
                send_file(sock, addr, command[1])  # Send file
                print("Ready for next command...")

        except socket.timeout:
            # Ignore timeouts in main loop
            continue

        except Exception as e:
            # Print any unexpected errors
            print(f"Error: {e}")


# Run the server if this script is executed directly
if __name__ == "__main__":
    main()
