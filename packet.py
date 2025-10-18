# packet.py
import struct
import zlib

HEADER_FORMAT = "!IIHH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

class Packet:
    def __init__(self, seq_num, ack_num, flags, payload=b''):
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.flags = flags  # 0 = DATA, 1 = ACK
        self.payload = payload

    def to_bytes(self):
        header = struct.pack(HEADER_FORMAT, self.seq_num, self.ack_num, self.flags, len(self.payload))
        checksum = zlib.crc32(header + self.payload)
        return struct.pack("!I", checksum) + header + self.payload