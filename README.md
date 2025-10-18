# compnetproject

# Team Information
  Group members:
  
    -Bao Phuc Nguyen
  
    -Chikwanine Kasali
  
    -Josiah Leija
  
    -Renatha Sanchez

  Selected Topic: Mini-FTP

# Project Overview
  Our goal is to Mini-FTP application over a custom reliable data transport protocol on top of UDP. This project aims to demonstrate how a reliable file transfer system can be built without relying on TCP, showcasing our understanding of transport protocols, error handling, and application-layer design.

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
