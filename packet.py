# packet.py

# Import the struct module, which is used for converting between Python values and C structs represented as bytes
import struct

# Import the zlib module to compute CRC32 checksums for data integrity
import zlib

# Constants representing different packet types or flags
DATA = 0  # Flag for a data packet
ACK = 1  # Flag for an acknowledgment packet
EOT = 0xFF  # Flag for "End of Transmission" packet

# Define the format of the packet header using struct format codes
# "!IIHH" means:
#   !    -> network byte order (big-endian)
#   I    -> unsigned int (4 bytes) for sequence number
#   I    -> unsigned int (4 bytes) for acknowledgment number
#   H    -> unsigned short (2 bytes) for flags
#   H    -> unsigned short (2 bytes) for payload length
HEADER_FORMAT = "!IIHH"

# Calculate the total size of the header in bytes
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


# Define a Packet class to represent a network packet
class Packet:
    # Constructor to create a packet object
    def __init__(self, seq_num, ack_num, flags, payload=b''):
        self.seq_num = seq_num  # Sequence number of the packet
        self.ack_num = ack_num  # Acknowledgment number of the packet
        self.flags = flags  # Flags indicating packet type (DATA, ACK, EOT)
        self.payload = payload  # The actual data carried by the packet (bytes)

    # Method to convert the packet object into bytes for sending over a network
    def to_bytes(self):
        # Pack the header fields (sequence number, ack number, flags, payload length) into bytes
        header = struct.pack(HEADER_FORMAT, self.seq_num, self.ack_num, self.flags, len(self.payload))

        # Compute CRC32 checksum of the header + payload for integrity checking
        checksum = zlib.crc32(header + self.payload)

        # Return the packet as bytes: checksum (4 bytes) + header + payload
        return struct.pack("!I", checksum) + header + self.payload

    # Static method to create a Packet object from raw bytes
    @staticmethod
    def from_bytes(data):
        # Extract the first 4 bytes as the checksum (network order)
        checksum_recv = struct.unpack("!I", data[:4])[0]

        # Extract the header part of the packet (next HEADER_SIZE bytes)
        header = data[4:4 + HEADER_SIZE]

        # Unpack the header into its fields
        seq_num, ack_num, flags, payload_len = struct.unpack(HEADER_FORMAT, header)

        # Extract the payload from the remaining bytes
        payload = data[4 + HEADER_SIZE:]

        # Check if the extracted payload length matches the length specified in the header
        if len(payload) != payload_len:
            raise ValueError("Payload length mismatch")  # Raise an error if lengths do not match

        # Calculate the checksum of the header + payload to verify integrity
        checksum_calc = zlib.crc32(header + payload)

        # Compare the calculated checksum with the received checksum
        if checksum_calc != checksum_recv:
            raise ValueError("Checksum mismatch")  # Raise an error if checksum does not match

        # Return a new Packet object with the extracted fields
        return Packet(seq_num, ack_num, flags, payload)
