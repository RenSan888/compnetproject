# ftp_client.py
# ----------------------------
# UDP-based FTP client using Go-Back-N (GBN) protocol
# Handles file uploads, downloads, and server directory listing
# ----------------------------

import socket
import os
from packet import Packet, DATA, ACK, EOT  # Packet structure and constants
from gbn_protocol import GBNProtocol        # Go-Back-N reliable protocol implementation

# ----------------------------
# Progress bar helper function
# ----------------------------
def progress_bar(current, total, prefix=""):
    """
    Display a simple ASCII progress bar in the terminal.

    Args:
        current (int): Current amount of progress (bytes processed, etc.)
        total (int): Total amount of progress possible.
        prefix (str): Optional label printed before the bar.

    Behavior:
        - Computes percentage complete.
        - Draws a 30-character bar of '=' (done) and '-' (remaining).
        - Uses carriage return '\r' to overwrite the same line.
        - 'end=""' prevents newline, 'flush=True' forces immediate update.
    """
    bar_len = 30                                     # Total bar width in characters
    filled = int(bar_len * current / total)          # Compute completed portion
    bar = "=" * filled + "-" * (bar_len - filled)    # Render bar string
    percent = (current / total) * 100                # Calculate percentage
    print(f"\r{prefix} [{bar}] {percent:5.1f}% ",   # Display bar
          end="", flush=True)

# ----------------------------
# File upload
# ----------------------------
def upload(sock, server_addr, filename):
    """
    Upload a file to the server using Go-Back-N protocol.

    Steps:
        1. Validate file exists locally.
        2. Send 'PUT <filename>' command to server.
        3. Wait for 'OK' response.
        4. Read file in 1024-byte chunks.
        5. Initialize GBNProtocol instance for reliable sending.
        6. Show a progress bar (visual only).
        7. Transmit chunks reliably using GBNProtocol.
    """

    # Step 1: Validate file existence
    if not os.path.exists(filename):
        print("File not found.")
        return
    filesize = os.path.getsize(filename)  # For progress bar only

    # Step 2: Inform server of upcoming upload
    sock.sendto(f"PUT {filename}".encode(), server_addr)

    # Step 3: Wait for server approval
    resp, _ = sock.recvfrom(1024)
    if resp != b"OK":
        print("Server refused file upload.")
        return

    # Step 4: Read file in chunks
    chunks = []
    with open(filename, "rb") as f:
        while chunk := f.read(1024):  # 1 KB per chunk
            chunks.append(chunk)

    # Step 5: Initialize Go-Back-N sender
    gbn = GBNProtocol(sock, server_addr)

    print(f"Uploading {filename} ({filesize} bytes)")
    sent_bytes = 0

    # Step 6: Visual progress bar before actual sending
    wrapped_chunks = []  # Used only for display
    for c in chunks:
        wrapped_chunks.append(c)
        sent_bytes += len(c)
        progress_bar(sent_bytes, filesize, prefix="Uploading")
    print()  # Move to new line after progress bar

    # Step 7: Send file reliably via GBN
    gbn.send_data(chunks)
    print("Upload complete.")

# ----------------------------
# File download
# ----------------------------
def download(sock, server_addr, filename):
    """
    Download a file from the server using Go-Back-N protocol.

    Steps:
        1. Send GET command.
        2. Wait for 'OK'.
        3. Receive Packet objects in sequence.
        4. Write data to local file.
        5. ACK every received packet.
        6. Stop at EOT packet.

    Notes:
        - File size unknown; fake progress bar used.
        - Timeout used to detect stalled or aborted transfers.
    """

    # Step 1: Request file
    sock.sendto(f"GET {filename}".encode(), server_addr)

    # Step 2: Wait for server approval
    resp, _ = sock.recvfrom(1024)
    if resp != b"OK":
        print("Server refused file download.")
        return

    expected_seq = 0                 # Next expected sequence number
    sock.settimeout(3)               # Timeout for recv

    downloaded_bytes = 0             # Progress bar tracking
    est_total = 1_000_000            # Estimated total for progress visualization

    print(f"Downloading {filename} ...")

    # Step 3: Receive packets in loop
    with open(filename, "wb") as f:
        while True:
            try:
                data, _ = sock.recvfrom(4096)  # Receive raw UDP packet
            except socket.timeout:
                # No packet for 3 sec → abort download
                print("\nServer stopped sending. Download aborted.")
                break

            try:
                # Parse packet from bytes
                packet = Packet.from_bytes(data)

                # Step 4: Accept only in-order packets
                if packet.seq_num == expected_seq:

                    # Detect EOT (End Of Transmission)
                    if packet.flags == EOT:
                        ack = Packet(0, packet.seq_num, ACK)
                        sock.sendto(ack.to_bytes(), server_addr)
                        print("\nDownload complete.")
                        break

                    # Normal data packet: write payload
                    f.write(packet.payload)
                    downloaded_bytes += len(packet.payload)
                    expected_seq += 1

                    # Update fake progress bar
                    progress_bar(downloaded_bytes, est_total, prefix="Downloading")

                # Step 5: ACK received packet (even out-of-order)
                ack = Packet(0, packet.seq_num, ACK)
                sock.sendto(ack.to_bytes(), server_addr)

            except Exception:
                # Ignore checksum, malformed packet errors
                continue

    print()
    sock.settimeout(None)  # Restore blocking socket

# ----------------------------
# List server files
# ----------------------------
def list_files(sock, server_addr):
    """
    Request a directory listing from the server.

    Steps:
        1. Send LIST command.
        2. Receive server directory data.
        3. Print result to terminal.
    """
    sock.sendto(b"LIST", server_addr)
    data, _ = sock.recvfrom(65536)  # Large buffer to hold many files
    print("Files on server:\n" + data.decode())

# ----------------------------
# Main client shell
# ----------------------------
def main():
    """
    Entry point for FTP client shell.

    Behavior:
        - Creates UDP socket
        - Loops: reads commands, dispatches PUT/GET/LIST
        - Exits on 'exit' or 'quit'
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_addr = ("127.0.0.1", 9000)  # Server target

    while True:
        command = input("ftp> ").strip()

        if command.startswith("PUT "):
            # Upload a file
            upload(sock, server_addr, command.split()[1])
        elif command.startswith("GET "):
            # Download a file
            download(sock, server_addr, command.split()[1])
        elif command == "LIST":
            # Show server directory
            list_files(sock, server_addr)
        elif command in ("exit", "quit"):
            # Exit client
            print("Goodbye")
            break

# Run only if script executed directly
if __name__ == "__main__":
    main()


# Example:
# GET C:\Users\NAME\Downloads\file.txt

#download file to your computer
#ftp> GET C:\Users\NAME\Downloads\file.txt

#=======================#
#=======COMMANDS========#
# LIST
# PUT C:\Users\NAME\Downloads\example.png
# PUT C:\Users\NAME\Documents\test1.txt
# PUT C:\Users\NAME\Downloads\example2.bin
# PUT C:\Users\NAME\Downloads\nofile.png
# PUT
# GET example.png
# GET missingtext.txt
# GET C:\Users\NAME\Downloads\test1.txt
#=======================#
