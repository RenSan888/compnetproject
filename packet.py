# packet.py
import struct   # Provides methods to convert between Python values and C structs (binary data)
import zlib     # Used here for CRC32 checksum calculation for data integrity

# Define the header format:
# !   → network (big-endian) byte order
# II  → two unsigned 32-bit integers (sequence and acknowledgment numbers)
# HH  → two unsigned 16-bit integers (flags and payload length)
HEADER_FORMAT = "!IIHH"

# Calculate header size in bytes (useful for parsing incoming packets)
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

class Packet:
    def __init__(self, seq_num, ack_num, flags, payload=b''):
        # Sequence number identifies this packet
        self.seq_num = seq_num

        # Acknowledgment number acknowledges receipt of packets up to this number
        self.ack_num = ack_num

        # Flags can indicate type of packet:
        # 0 = DATA packet, 1 = ACK packet, 0xFF = End-of-Transmission marker
        self.flags = flags

        # Actual data being carried by this packet
        self.payload = payload

    def to_bytes(self):
        """Convert this Packet into a bytes object suitable for sending via UDP."""
        # Build the header according to the defined structure
        header = struct.pack(HEADER_FORMAT, self.seq_num, self.ack_num, self.flags, len(self.payload))

        # Calculate a CRC32 checksum over the header + payload to detect corruption
        checksum = zlib.crc32(header + self.payload)

        # Final packet = checksum (4 bytes) + header + payload
        return struct.pack("!I", checksum) + header + self.payload

    @staticmethod
    def from_bytes(data):
        """Recreate a Packet object from a bytes sequence (received over the network)."""
        # Extract first 4 bytes — the checksum field
        checksum_recv = struct.unpack("!I", data[:4])[0]

        # Extract header portion based on HEADER_SIZE
        header = data[4:4 + HEADER_SIZE]

        # Unpack header fields (sequence, ack, flags, payload length)
        seq_num, ack_num, flags, payload_len = struct.unpack(HEADER_FORMAT, header)

        # Extract payload (remaining bytes after header)
        payload = data[4 + HEADER_SIZE:]

        # Recompute checksum locally for verification
        checksum_calc = zlib.crc32(header + payload)

        # Verify data integrity — raise error if mismatch
        if checksum_calc != checksum_recv:
            raise ValueError("Checksum mismatch (data corrupted)")

        # Return a new Packet instance built from parsed values
        return Packet(seq_num, ack_num, flags, payload)
