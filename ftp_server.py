# ftp_server.py
# ----------------------------
# UDP-based FTP server using Go-Back-N (GBN) protocol
# Handles file uploads, downloads, and directory listing
# ----------------------------

import socket
import os
import time
from packet import Packet, DATA, ACK, EOT
from gbn_protocol import GBNProtocol

# ----------------------------
# Receive/upload a file from client
# ----------------------------
def save_file(sock, addr, filename):
    """
    Receive a file from a client using Go-Back-N protocol.

    Args:
        sock (socket.socket): The UDP socket to communicate over.
        addr (tuple): Client address (IP, port).
        filename (str): Name of the file to save locally.

    Behavior:
        - Uses 'expected_seq' to accept only in-order packets.
        - Writes payload to file as packets arrive.
        - Sends ACK for every packet received.
        - Detects EOT (End Of Transmission) to finish transfer.
        - Uses a timeout mechanism (5s) to detect client inactivity.
    """
    # Extract just the filename (ignore any path from client)
    filename = os.path.basename(filename)
    print(f"Receiving file: {filename}")

    expected_seq = 0               # Next expected sequence number
    last_packet_time = time.time() # Timestamp of last received packet
    sock.settimeout(1)             # Check for packets every 1 second

    with open(filename, "wb") as f:  # Open file for writing in binary mode
        while True:
            try:
                data, _ = sock.recvfrom(4096)  # Receive raw UDP packet
            except socket.timeout:
                # If no packets received for >5 seconds, abort
                if time.time() - last_packet_time > 5:
                    print("Client stopped sending. Transfer aborted.")
                    break
                continue  # Otherwise, continue waiting

            last_packet_time = time.time()  # Update timestamp

            try:
                # Convert raw bytes to Packet object
                packet = Packet.from_bytes(data)

                # Only accept packets with expected sequence number
                if packet.seq_num == expected_seq:
                    # EOT packet signals transfer complete
                    if packet.flags == EOT:
                        ack = Packet(0, packet.seq_num, ACK)  # Final ACK
                        sock.sendto(ack.to_bytes(), addr)
                        print("File transfer complete.")
                        break

                    # Write payload to file
                    f.write(packet.payload)
                    expected_seq += 1  # Increment expected sequence number

                # Always send ACK, even for out-of-order packet
                ack = Packet(0, packet.seq_num, ACK)
                sock.sendto(ack.to_bytes(), addr)

            except Exception:
                # Ignore malformed packets
                continue

    sock.settimeout(None)  # Restore blocking mode on socket

# ----------------------------
# Send/download a file to client
# ----------------------------
def send_file(sock, addr, filename):
    """
    Send a file to a client using Go-Back-N protocol.

    Args:
        sock (socket.socket): UDP socket to send data through.
        addr (tuple): Client address (IP, port).
        filename (str): File to read and transmit.

    Behavior:
        - Reads file in 1024-byte chunks.
        - Uses GBNProtocol to send data reliably over UDP.
        - ACK handling done by GBNProtocol internally.
    """
    if not os.path.exists(filename):
        print("File not found.")
        return

    # Step 1: Read file into chunks
    chunks = []
    with open(filename, "rb") as f:
        while chunk := f.read(1024):  # 1 KB per chunk
            chunks.append(chunk)

    # Step 2: Initialize Go-Back-N sender
    gbn = GBNProtocol(sock, addr)
    gbn.send_data(chunks)  # Send file reliably

# ----------------------------
# Handle LIST command
# ----------------------------
def handle_list(sock, addr):
    """
    Send directory listing to client.

    Args:
        sock (socket.socket): UDP socket to respond through.
        addr (tuple): Client address.

    Behavior:
        - Lists files in current directory.
        - Joins filenames with newline characters.
        - Sends as bytes over UDP.
    """
    files = os.listdir('.')          # Get files in current directory
    files_str = '\n'.join(files)     # Join into single string
    sock.sendto(files_str.encode(), addr)  # Send to client

# ----------------------------
# Main server loop
# ----------------------------
def main():
    """
    Main server loop.

    Behavior:
        - Creates UDP socket and binds to localhost:9000.
        - Waits for incoming commands (PUT, GET, LIST).
        - Dispatches commands to proper handlers.
        - Sends acknowledgment (OK) before file transfer starts.
        - Keeps server running even on errors.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 9000))  # Bind to local UDP port
    print("Server listening on UDP port 9000...")

    while True:
        try:
            data, addr = sock.recvfrom(2048)        # Receive client command
            command_text = data.decode(errors="ignore").strip()
            command = command_text.split()          # Split into command + args

            if not command:
                continue  # Ignore empty commands

            if command[0] == "PUT":
                # Ensure filename provided
                if len(command) < 2:
                    sock.sendto(b"ERR Missing filename", addr)
                    continue
                sock.sendto(b"OK", addr)             # Approve upload
                save_file(sock, addr, command[1])   # Receive file

            elif command[0] == "GET":
                if len(command) < 2:
                    sock.sendto(b"ERR Missing filename", addr)
                    continue
                sock.sendto(b"OK", addr)             # Approve download
                send_file(sock, addr, command[1])   # Send file

            elif command[0] == "LIST":
                handle_list(sock, addr)              # Send directory listing

        except Exception as e:
            # Log errors without crashing
            print(f"Error: {e}")

# Only run server if script executed directly
if __name__ == "__main__":
    main()
