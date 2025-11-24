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

    Created gbn_protocol.py, ftp_server.py, and ftp_client.py

What Remains to Be Completed:

from_bytes Method:

    Required to deserialize a received byte stream back into a Packet object.
    
    Needs to validate checksum, extract fields, and handle any errors (e.g., corrupted or truncated data).

Input Validation / Error Handling:

    The class currently assumes valid inputs.
    
    Could be extended with basic validation (e.g., checking payload size, verifying flags).

Remaining Classes (COMPLETED):

    gbn_protocol.py (Go-Back)
  
    ftp_server.py
    
    ftp_client.py
  

# To-do List 11/24/2025
1. Transport Layer / Protocol

     Optional: Add SYN/FIN flags for connection-like behavior.
    
     Optional: Adjust checksum to 2 bytes if strictly following spec.
    
     Optional: Implement adaptive timeout based on RTT.

2. Application Layer

     Implement LIST command:
    
    Server: send a list of files in the working directory.
    
    Client: display received file list.
    
     Optional: Input validation (e.g., filename exists, command syntax).

3. Concurrency

     Modify server to support multiple clients simultaneously:
    
    Each client session (PUT/GET/LIST) should run in a separate thread.

4. Metrics & Testing

     Track and report:
    
    Throughput (bytes/sec)
    
    Latency (time from request to completion)
    
    Retransmissions (count per transfer)
    
    File integrity (verify using SHA-256 hash)
    
    Completion rate (percentage of successful transfers)
    
     Test under network conditions:
    
    Clean network
    
    Random packet loss (5–10%)
    
    Bursty packet loss

5. Client-Server Improvements (Optional)

     Make QUIT command automatically send a shutdown signal to server if desired.
    
     Improve error messages / logging.
    
     Handle invalid packets more robustly.

# Common requirements (Also check for these requirements in the code)
  
  Transport (your custom protocol)
  
      Define a header including at least: ver, flags, conn_id, seq, ack, len, checksum.
      
          Implement reliability using one of the protocols from the textbook:
          
          Stop-and-Wait ARQ
          
          Go-Back-N
          
          Selective Repeat
          
          TCP-like stream protocol
  
      Implement flow control (receiver-advertised window).
      
      Implement timeout & retransmission (fixed RTO or RTT-based estimation).
      
      Provide a clean API for the app layer, e.g.:
      
          Message-oriented: connect(addr), send_msg(b), on_message(cb), close()
          
          Stream-oriented: connect(addr), write(b), read(n, timeout), close()
      
      Checksum required.
      
      Collect metrics:
  
          Throughput (goodput)
          
          Average/95th-percentile latency
          
          Retransmissions per KB
  
    Application (the service you choose below)
    
        Define message grammar (text-based commands or lightweight binary).
        
        Handle errors (invalid commands, disconnects).
        
        Concurrency: serve ≥ 2 clients concurrently.

# Testing Profiles

    Clean Profile – minimal loss (0–1%) and low jitter.
    
    Random Loss Profile – random packet loss (5–10%).
    
    Bursty Loss Profile – burst losses averaging 8–12%.
    
    Your implementation must function correctly under all three profiles. Performance should degrade gracefully under loss but must not crash or hang.

