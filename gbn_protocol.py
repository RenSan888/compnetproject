# gbn_protocol.py
import threading  # Used for running ACK receiver in a separate thread
import time
from packet import Packet

# Define constants for Go-Back-N behavior
WINDOW_SIZE = 5     # Max number of unacknowledged packets allowed
TIMEOUT = 1.0       # Time in seconds before retransmission on timeout

class GBNProtocol:
    """Implements Go-Back-N ARQ protocol for reliable data transfer over UDP."""

    def __init__(self, sock, address):
        self.sock = sock                   # UDP socket used for sending/receiving
        self.address = address             # Destination address (IP, port)
        self.base = 0                      # Oldest unacknowledged packet sequence number
        self.next_seq = 0                  # Next sequence number to send
        self.window = {}                   # Store sent but unacknowledged packets
        self.lock = threading.Lock()       # Ensure thread-safe access to shared variables
        self.timer = None                  # Timer for retransmissions
        self.running = True                # Control flag for receiver thread

    def start_timer(self):
        """Start or restart the retransmission timer."""
        # Cancel existing timer (if running)
        if self.timer:
            self.timer.cancel()
        # Create a new timer that calls self.timeout() after TIMEOUT seconds
        self.timer = threading.Timer(TIMEOUT, self.timeout)
        self.timer.start()

    def timeout(self):
        """Called when timer expires — resend all unacknowledged packets."""
        with self.lock:
            print("Timeout — resending current window of packets...")
            # Resend all packets currently in window (oldest to newest)
            for seq in sorted(self.window):
                self.sock.sendto(self.window[seq].to_bytes(), self.address)
            # Restart timer after resending
            self.start_timer()

    def send_data(self, data_chunks):
        """
        Send a list of data chunks using Go-Back-N.
        Spawns a receiver thread to listen for ACKs concurrently.
        """
        # Start separate thread to listen for acknowledgments
        recv_thread = threading.Thread(target=self.recv_acks)
        recv_thread.start()

        # Iterate over all data chunks to send
        for chunk in data_chunks:
            # Wait if window is full (i.e., next_seq outside base + WINDOW_SIZE)
            while self.next_seq >= self.base + WINDOW_SIZE:
                time.sleep(0.01)  # Yield CPU briefly

            # Create a new data packet
            packet = Packet(self.next_seq, 0, 0, chunk)

            with self.lock:
                # Send packet over UDP
                self.sock.sendto(packet.to_bytes(), self.address)
                # Store in window for possible retransmission
                self.window[self.next_seq] = packet

                # If this is the first unacknowledged packet, start timer
                if self.base == self.next_seq:
                    self.start_timer()

                # Increment next sequence number
                self.next_seq += 1

        # After all chunks are sent, send a special “end-of-transfer” packet (flag = 0xFF)
        while self.next_seq >= self.base + WINDOW_SIZE:
            time.sleep(0.01)

        packet = Packet(self.next_seq, 0, 0xFF, b'')
        with self.lock:
            self.sock.sendto(packet.to_bytes(), self.address)
            self.window[self.next_seq] = packet
            self.next_seq += 1

        # Wait until ACK receiver finishes
        recv_thread.join()

    def recv_acks(self):
        """Continuously listen for ACKs and slide the window accordingly."""
        while self.running:
            try:
                # Receive raw packet bytes
                data, _ = self.sock.recvfrom(1024)
                ack = Packet.from_bytes(data)  # Decode ACK

                with self.lock:
                    # Check if valid ACK and matches a packet in window
                    if ack.flags == 1 and ack.ack_num in self.window:
                        # Remove acknowledged packet
                        del self.window[ack.ack_num]

                        # Slide the base forward if it was the oldest unacknowledged packet
                        if ack.ack_num == self.base:
                            while self.base not in self.window and self.base < self.next_seq:
                                self.base += 1

                            # If all packets are acknowledged, stop timer and end thread
                            if self.base == self.next_seq:
                                if self.timer:
                                    self.timer.cancel()
                                self.running = False
                            else:
                                # Restart timer for next pending packet
                                self.start_timer()
            except Exception:
                # Ignore network errors or malformed packets
                continue
