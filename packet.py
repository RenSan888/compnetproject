# packet.py
import struct  # For packing/unpacking binary data
import zlib    # For checksum calculation (CRC32)

# Header format: Sequence number (I), Ack number (I), Flags (H), Payload length (H)
HEADER_FORMAT = "!IIHH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # Calculate header size in bytes

class Packet:
    def __init__(self, seq_num, ack_num, flags, payload=b''):
        self.seq_num = seq_num        # Packet sequence number
        self.ack_num = ack_num        # Acknowledgment number
        self.flags = flags            # Packet type: 0 = DATA, 1 = ACK
        self.payload = payload        # Data payload

    def to_bytes(self):
        """Serialize packet to bytes for sending over the network."""
        header = struct.pack(HEADER_FORMAT, self.seq_num, self.ack_num, self.flags, len(self.payload))
        checksum = zlib.crc32(header + self.payload)  # CRC32 checksum for integrity
        return struct.pack("!I", checksum) + header + self.payload

    @staticmethod
    def from_bytes(data):
        """Deserialize bytes back into a Packet object."""
        checksum_recv = struct.unpack("!I", data[:4])[0]  # Extract received checksum
        header = data[4:4 + HEADER_SIZE]                  # Extract header
        seq_num, ack_num, flags, payload_len = struct.unpack(HEADER_FORMAT, header)
        payload = data[4 + HEADER_SIZE:]                 # Extract payload
        checksum_calc = zlib.crc32(header + payload)     # Compute checksum
        if checksum_calc != checksum_recv:               # Verify integrity
            raise ValueError("Checksum mismatch")
        return Packet(seq_num, ack_num, flags, payload)
