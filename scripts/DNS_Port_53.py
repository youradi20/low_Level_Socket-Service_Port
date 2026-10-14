#!/usr/bin/env python3
"""
Script 5: DNS Port 53 — Raw UDP Socket Client
Objective: Construct a raw DNS query packet manually (binary),
           send via UDP socket, receive & parse the response.

Modules used: socket, struct, random (built-in only)
Prohibited: dnslib, dnspython, socket.getaddrinfo
"""

import socket
import struct
import random


# -----------------------------------------------------------
# DNS Record Type Map
# -----------------------------------------------------------
TYPE_NAMES = {
    1: "A",      2: "NS",     5: "CNAME",  6: "SOA",
    12: "PTR",   15: "MX",    16: "TXT",   28: "AAAA",
    33: "SRV",   41: "OPT",   43: "DS",    46: "RRSIG",
    48: "DNSKEY", 52: "TLSA",
}
CLASS_NAMES = {1: "IN", 3: "CH", 4: "HS", 255: "ANY"}


# -----------------------------------------------------------
# HELPER: Encode domain name into DNS wire format
# -----------------------------------------------------------
#   "example.com"  →  \x07example\x03com\x00
#
#   Each label is prefixed with its byte length,
#   terminated by a zero-length root label.
# -----------------------------------------------------------
def encode_domain_name(domain):
    encoded = b""
    for label in domain.split("."):
        encoded += bytes([len(label)]) + label.encode("ascii")
    encoded += b"\x00"  # Root label (zero length)
    return encoded


# -----------------------------------------------------------
# HELPER: Parse a domain name from DNS response
#         Handles compression pointers (RFC 1035 §4.1.4)
#
#   Pointer format: first two bits = 11 (0xC0)
#   Remaining 14 bits = offset into packet
# -----------------------------------------------------------
def parse_name(data, offset):
    labels = []
    jumped = False
    return_offset = offset
    jumps = 0

    while True:
        if offset >= len(data):
            break

        length = data[offset]

        # Check for compression pointer (top 2 bits = 11)
        if (length & 0xC0) == 0xC0:
            if not jumped:
                return_offset = offset + 2
            pointer = struct.unpack("!H", data[offset:offset + 2])[0] & 0x3FFF
            offset = pointer
            jumped = True
            jumps += 1
            if jumps > 20:  # Prevent infinite loops
                break

        # Zero-length label = end of name
        elif length == 0:
            offset += 1
            break

        # Regular label
        else:
            offset += 1
            label = data[offset:offset + length].decode("ascii", errors="replace")
            labels.append(label)
            offset += length

    if jumped:
        offset = return_offset

    return offset, ".".join(labels)


# -----------------------------------------------------------
# HELPER: Format RDATA as human-readable string
# -----------------------------------------------------------
def format_rdata(rdata, rtype, full_packet):
    """Convert raw RDATA bytes to a readable string."""
    try:
        if rtype == 1:        # A record → IPv4 address
            return ".".join(str(b) for b in rdata)

        elif rtype == 28:     # AAAA record → IPv6 address
            parts = []
            for i in range(0, 16, 2):
                parts.append(format(struct.unpack("!H", rdata[i:i + 2])[0], "x"))
            return ":".join(parts)

        elif rtype == 5:      # CNAME → domain name
            _, name = parse_name(full_packet, 0)
            # For CNAME, rdata starts with name; use full packet for pointers
            # Re-parse from the rdata offset within full_packet
            return f"{name} (CNAME)"

        elif rtype == 15:     # MX → preference + exchange
            preference = struct.unpack("!H", rdata[:2])[0]
            _, exchange = parse_name(full_packet, 0)
            return f"{preference} {exchange}"

        elif rtype == 2:      # NS → domain name
            _, name = parse_name(full_packet, 0)
            return name

        elif rtype == 16:     # TXT → text strings
            text = ""
            i = 0
            while i < len(rdata):
                txt_len = rdata[i]
                i += 1
                text += rdata[i:i + txt_len].decode("utf-8", errors="replace")
                i += txt_len
            return f'"{text}"'

        else:
            return rdata.hex()

    except Exception:
        return rdata.hex()


# -----------------------------------------------------------
# BUILD: Construct a DNS query packet
# -----------------------------------------------------------
def build_dns_query(domain, qtype=1, qclass=1):
    """
    Build a raw DNS query packet (binary bytes).

    DNS Header (12 bytes):
      +----------------+----------------+
      |  ID (16 bits)  |  Flags (16)    |
      +----------------+----------------+
      | QDCOUNT (16)   | ANCOUNT (16)   |
      +----------------+----------------+
      | NSCOUNT (16)   | ARCOUNT (16)   |
      +----------------+----------------+

    Flags for standard query:
      QR=0, Opcode=0, AA=0, TC=0, RD=1, RA=0, Z=0, RCODE=0
      → 0x0100
    """
    # Header
    tx_id = random.randint(0, 65535)
    flags = 0x0100        # Standard query, RD (Recursion Desired) = 1
    qdcount = 1           # 1 question
    ancount = 0           # 0 answers (we're querying)
    nscount = 0
    arcount = 0

    header = struct.pack(
        "!HHHHHH",
        tx_id, flags, qdcount, ancount, nscount, arcount
    )

    # Question section
    qname = encode_domain_name(domain)
    question = struct.pack("!HH", qtype, qclass)

    packet = header + qname + question
    return packet, tx_id


# -----------------------------------------------------------
# PARSE: Parse a DNS response packet
# -----------------------------------------------------------
def parse_dns_response(data, raw_packet):
    """Parse a complete DNS response packet."""
    # Header (12 bytes)
    tx_id, flags, qdcount, ancount, nscount, arcount = struct.unpack(
        "!HHHHHH", data[:12]
    )

    # Extract flag fields
    qr = (flags >> 15) & 1          # 0=query, 1=response
    opcode = (flags >> 11) & 0xF    # 0=standard query
    aa = (flags >> 10) & 1          # Authoritative Answer
    tc = (flags >> 9) & 1           # Truncated
    rd = (flags >> 8) & 1           # Recursion Desired
    ra = (flags >> 7) & 1           # Recursion Available
    rcode = flags & 0xF             # Response Code

    RCODE_NAMES = {
        0: "NOERROR", 1: "FORMERR", 2: "SERVFAIL",
        3: "NXDOMAIN", 4: "NOTIMP", 5: "REFUSED"
    }

    # Question section
    offset = 12
    questions = []
    for _ in range(qdcount):
        offset, qname = parse_name(data, offset)
        qtype, qclass = struct.unpack("!HH", data[offset:offset + 4])
        offset += 4
        questions.append({
            "name": qname,
            "type": qtype,
            "class": qclass,
        })

    # Answer section
    answers = []
    for _ in range(ancount):
        offset, name = parse_name(data, offset)
        rtype, rclass, ttl, rdlength = struct.unpack("!HHIH", data[offset:offset + 10])
        offset += 10
        rdata = data[offset:offset + rdlength]
        offset += rdlength

        # Format the RDATA
        rdata_str = format_rdata(rdata, rtype, raw_packet)
        # For A records, we can format directly
        if rtype == 1:
            rdata_str = ".".join(str(b) for b in rdata)
        elif rtype == 28:
            parts = []
            for i in range(0, len(rdata), 2):
                parts.append(format(struct.unpack("!H", rdata[i:i + 2])[0], "x"))
            rdata_str = ":".join(parts)

        answers.append({
            "name": name,
            "type": rtype,
            "type_name": TYPE_NAMES.get(rtype, f"TYPE{rtype}"),
            "class": rclass,
            "class_name": CLASS_NAMES.get(rclass, f"CLASS{rclass}"),
            "ttl": ttl,
            "rdlength": rdlength,
            "rdata": rdata,
            "rdata_str": rdata_str,
        })

    return {
        "id": tx_id,
        "qr": qr,
        "opcode": opcode,
        "aa": aa,
        "tc": tc,
        "rd": rd,
        "ra": ra,
        "rcode": rcode,
        "rcode_name": RCODE_NAMES.get(rcode, f"RCODE{rcode}"),
        "qdcount": qdcount,
        "ancount": ancount,
        "nscount": nscount,
        "arcount": arcount,
        "questions": questions,
        "answers": answers,
    }


# -----------------------------------------------------------
# MAIN: DNS Query via Raw UDP Socket
# -----------------------------------------------------------
def dns_query_via_port_53(
    domain="example.com",
    qtype=1,
    dns_server="8.8.8.8",
    port=53,
):
    # =======================================================
    # STEP 1: Build the DNS query packet (binary)
    # =======================================================
    type_name = TYPE_NAMES.get(qtype, f"TYPE{qtype}")
    print(f"[+] Building DNS query packet for '{domain}' ({type_name} record) ...")

    query_packet, tx_id = build_dns_query(domain, qtype)
    print(f"[+] Transaction ID: 0x{tx_id:04X}")
    print(f"[+] Query packet size: {len(query_packet)} bytes")
    print(f"[+] Query hex dump: {query_packet.hex()}")

    # =======================================================
    # STEP 2: Create UDP socket and send query
    # =======================================================
    print(f"\n[+] Creating UDP socket (SOCK_DGRAM) ...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)

    print(f"[+] Sending query to {dns_server}:{port} ...")
    sock.sendto(query_packet, (dns_server, port))

    # =======================================================
    # STEP 3: Receive response
    # =======================================================
    print(f"[+] Waiting for response ...")
    response_data, server_addr = sock.recvfrom(4096)
    sock.close()

    print(f"[+] Received {len(response_data)} bytes from {server_addr}")
    print(f"[+] Response hex dump: {response_data.hex()}")

    # =======================================================
    # STEP 4: Parse the response
    # =======================================================
    print(f"\n[+] Parsing DNS response ...")
    parsed = parse_dns_response(response_data, response_data)

    # =======================================================
    # STEP 5: Print formatted output
    # =======================================================
    print(f"\n{'='*60}")
    print(f"  DNS RESPONSE HEADER")
    print(f"{'='*60}")
    print(f"  Transaction ID:  0x{parsed['id']:04X}")
    print(f"  Query/Response:  {'Response' if parsed['qr'] else 'Query'}")
    print(f"  Opcode:          {parsed['opcode']}")
    print(f"  Authoritative:   {'Yes' if parsed['aa'] else 'No'}")
    print(f"  Truncated:       {'Yes' if parsed['tc'] else 'No'}")
    print(f"  Recursion Desired: {'Yes' if parsed['rd'] else 'No'}")
    print(f"  Recursion Available: {'Yes' if parsed['ra'] else 'No'}")
    print(f"  Response Code:   {parsed['rcode_name']} ({parsed['rcode']})")
    print(f"  Questions:       {parsed['qdcount']}")
    print(f"  Answers:         {parsed['ancount']}")
    print(f"  Authority:       {parsed['nscount']}")
    print(f"  Additional:      {parsed['arcount']}")

    print(f"\n{'='*60}")
    print(f"  QUESTION SECTION")
    print(f"{'='*60}")
    for q in parsed["questions"]:
        qtype_name = TYPE_NAMES.get(q["type"], f"TYPE{q['type']}")
        qclass_name = CLASS_NAMES.get(q["class"], f"CLASS{q['class']}")
        print(f"  {q['name']:30s} {qclass_name:5s} {qtype_name}")

    print(f"\n{'='*60}")
    print(f"  ANSWER SECTION")
    print(f"{'='*60}")
    if parsed["answers"]:
        for a in parsed["answers"]:
            print(
                f"  {a['name']:30s} {a['class_name']:5s} "
                f"{a['type_name']:6s} {a['ttl']:>7d}  {a['rdata_str']}"
            )
    else:
        print("  (no answers)")

    # Print the final resolved IP for A record queries
    if qtype == 1 and parsed["answers"]:
        for a in parsed["answers"]:
            if a["type"] == 1:
                print(f"\n[+] ✅ Resolved: {domain} → {a['rdata_str']}")

    print(f"\n[+] UDP socket closed. DNS query complete.")


# -----------------------------------------------------------
# Run multiple queries to demonstrate the protocol
# -----------------------------------------------------------
if __name__ == "__main__":
    # Query 1: A record for example.com
    print(f"\n{'#'*60}")
    print(f"  QUERY 1: A Record for example.com")
    print(f"{'#'*60}")
    dns_query_via_port_53(domain="example.com", qtype=1)

    # Query 2: A record for google.com
    print(f"\n\n{'#'*60}")
    print(f"  QUERY 2: A Record for google.com")
    print(f"{'#'*60}")
    dns_query_via_port_53(domain="google.com", qtype=1)

    # Query 3: AAAA record (IPv6) for example.com
    print(f"\n\n{'#'*60}")
    print(f"  QUERY 3: AAAA Record for example.com")
    print(f"{'#'*60}")
    dns_query_via_port_53(domain="example.com", qtype=28)
