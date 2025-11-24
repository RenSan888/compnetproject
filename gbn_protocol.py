# gbn_protocol.py

# Import threading to handle concurrent operations (sending and receiving simultaneously)
import threading

# Import time for sleep/delay functions
import time

# Import Packet class and constants (DATA, ACK, EOT) from packet.py
from packet import Packet, DATA, ACK, EOT

# Maximum number of unacknowledged packets allowed in the window
WINDOW_SIZE = 5

# Timeout duration in seconds for retransmitting unacknowledged packets
TIMEOUT = 1.0

# Go-Back-N Protocol implementation class
class GBNProtocol:
    # Constructor: initializes the protocol with a socket and destination address
    def __init__(self, sock, address):
        self.sock = sock              # UDP socket used for sending/receiving packets
        self.address = address        # Destination address (IP, port)
        self.base = 0                 # Sequence number of the oldest unacknowledged packet
        self.next_seq = 0             # Sequence number for the next packet to send
        self.window = {}              # Dictionary to store sent but unacknowledged packets
        self.lock = threading.Lock()  # Lock to synchronize access to shared data (window, base)
        self.timer = None             # Timer object for retransmissions
        self.running = True           # Flag to control protocol execution

    # Start or restart the retransmission timer
    def start_timer(self):
        if self.timer:
            self.timer.cancel()       # Cancel existing timer if it exists
        if self.window:               # Only start timer if there are unacknowledged packets
            self.timer = threading.Timer(TIMEOUT, self.timeout)  # Create a new timer
            self.timer.start()        # Start the timer

    # Timeout handler: called when a timer expires
    def timeout(self):
        with self.lock:               # Lock to safely access shared data
            if not self.window:       # If window is empty, no packets to resend
                return
            print("Timeout — resending current window...")  # Inform user of retransmission
            for seq in sorted(self.window):                 # Resend all packets in current window
                self.sock.sendto(self.window[seq].to_bytes(), self.address)
            self.start_timer()        # Restart timer after resending

    # Send a list of data chunks using Go-Back-N protocol
    def send_data(self, data_chunks):
        self.running = True           # Set running flag to True at start
        recv_thread = threading.Thread(target=self.recv_acks)  # Thread to receive ACKs concurrently
        recv_thread.start()           # Start the ACK receiving thread

        # Loop through all data chunks and send packets
        for chunk in data_chunks:
            # Wait if window is full
            while self.next_seq >= self.base + WINDOW_SIZE:
                time.sleep(0.01)      # Short sleep to prevent busy-waiting

            # Create a data packet with current sequence number
            packet = Packet(self.next_seq, 0, DATA, chunk)

            # Send packet and update window atomically
            with self.lock:
                self.sock.sendto(packet.to_bytes(), self.address)  # Send packet over UDP
                self.window[self.next_seq] = packet               # Store packet in window
                if self.base == self.next_seq:                    # If base equals next_seq, start timer
                    self.start_timer()
                self.next_seq += 1                                # Increment next sequence number

        # Send End-of-Transmission (EOT) packet after all data chunks
        while self.next_seq >= self.base + WINDOW_SIZE:
            time.sleep(0.01)      # Wait if window is full
        eot = Packet(self.next_seq, 0, EOT, b'')  # Create EOT packet
        with self.lock:
            self.sock.sendto(eot.to_bytes(), self.address)  # Send EOT packet
            self.window[self.next_seq] = eot                # Add EOT packet to window
            self.next_seq += 1

        recv_thread.join()  # Wait for the receiving thread to finish (all ACKs received)
        print("Transfer complete, returning to prompt.")  # Inform user that transfer is done

    # Thread method to receive ACKs and update the sending window
    def recv_acks(self):
        while self.running:          # Keep receiving while protocol is running
            try:
                data, _ = self.sock.recvfrom(1024)        # Receive raw data from socket
                ack = Packet.from_bytes(data)            # Convert bytes to Packet object
                with self.lock:                          # Lock to update shared variables safely
                    if ack.flags == ACK and ack.ack_num >= self.base:
                        # Cumulative ACK: remove all packets up to ack_num from window
                        for seq in list(self.window.keys()):
                            if seq <= ack.ack_num:
                                del self.window[seq]

                        self.base = ack.ack_num + 1      # Move base forward

                        if self.base == self.next_seq:  # If all packets acknowledged
                            if self.timer:
                                self.timer.cancel()     # Cancel the timer
                            self.running = False         # Stop receiving ACKs
                        else:
                            self.start_timer()           # Restart timer for remaining unacknowledged packets
            except Exception:               # Ignore exceptions (e.g., timeout, invalid packet)
                continue

