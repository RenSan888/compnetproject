# compnetproject

# Team Information
  Group members:
  
    -Bao Phuc Nguyen
  
    -Chikwanine Kasali
  
    -Josiah Leija
  
    -Renatha Sanchez

  Selected Topic: Mini-FTP

# Project Overview
  Our goal is to implement a Mini-FTP application over a custom reliable data transport protocol on top of UDP. This project aims to demonstrate how a reliable file transfer system can be built without relying on TCP, showcasing our understanding of transport protocols, error handling, and application-layer design. 

# Transport Protocol Design Plan
Packet Header Fields:

    Sequence Number (4 bytes)
    
    Acknowledgment Number (4 bytes)
    
    Flags (SYN, ACK, FIN, DATA)
    
    Payload Length (2 bytes)
    
    Checksum (2 bytes)

Timers:
  
    Per-connection timeout for retransmission.
    
    Adaptive timeout based on estimated RTT (optional).

Flow Control:

    Window size configurable (default: 5 packets).
    
    Sliding window maintained on sender.

Retransmission Logic:
  
    Timeout-based retransmission of the entire window.
    
    Cumulative ACKs supported.

Reliability Guarantees

    Packet Loss: Detected via timeout; triggers retransmission.
    
    Duplication: Duplicate sequence numbers are discarded.
    
    Reordering: GBN ensures in-order delivery; out-of-order packets are discarded.

# Application Layer Design Plan
Message Format & Commands

    Supported commands:
    
    LIST — Lists files available on the server.
    
    GET <filename> — Downloads a file from server to client.
    
    PUT <filename> — Uploads a file from client to server.

QUIT — Ends the client session.

    Client-Server Interaction
    
    Client sends commands to the server.
    
    Server parses the command and performs the corresponding file operation.
    
    Both client and server use our reliable GBN protocol over UDP for data exchange.

Concurrency
    
    Server uses multithreading or async IO to handle multiple clients concurrently (minimum 2).
    
    Each client connection is handled in a separate thread or async task.

# Testing and Metrics Plan
Test Environments
    
    We will simulate the following network conditions using tools like tc (Linux):
    
    Clean Network: No loss, delay, or reordering.
    
    Random Loss: Simulated packet loss (5%–10%).
    
    Bursty Loss: Groups of packets lost (e.g., 3-5 in a row).

Metrics to Collect

    Throughput: Bytes transferred per second.
    
    Latency: Time between request and completion.
    
    Retransmissions: Number of packets resent.
    
    File Integrity: Files checked with SHA-256 hashes.
    
    Completion Rate: Percentage of successful transfers.

# Progress Summary
What Has Been Implemented So Far:

    Packet Class Structure:
    The Packet class has been implemented to encapsulate key transport-layer information:
    
    seq_num: Sequence number
    
    ack_num: Acknowledgment number
    
    flags: Control flags (e.g., 0 = DATA, 1 = ACK)
    
    payload: The data carried by the packet

What Remains to Be Completed:

from_bytes Method:

    Required to deserialize a received byte stream back into a Packet object.
    
    Needs to validate checksum, extract fields, and handle any errors (e.g., corrupted or truncated data).

Input Validation / Error Handling:

    The class currently assumes valid inputs.
    
    Could be extended with basic validation (e.g., checking payload size, verifying flags).

This GitHub was created after making some of the code so the changes don't show who edited it.
