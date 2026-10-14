#!/usr/bin/env python3
"""
Script 3: FTP Port 21 — Raw Socket Client (PASV Mode)
Objective: Initiate control + data sockets in PASV mode,
           retrieve a file from an FTP server, and save locally.

Modules used: socket, re (built-in only)
Prohibited: ftplib, urllib
"""

import socket
import re


# -----------------------------------------------------------
# Helper: Create a TCP socket with timeout
# -----------------------------------------------------------
def create_tcp_socket(timeout=30):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    return sock


# -----------------------------------------------------------
# Helper: Read FTP response from control socket
# -----------------------------------------------------------
def read_response(ctrl_sock):
    response = b""
    while True:
        try:
            chunk = ctrl_sock.recv(4096)
            if not chunk:
                break
            response += chunk
            decoded = response.decode("utf-8", errors="replace")
            lines = decoded.splitlines()
            if lines and len(lines[-1]) >= 4:
                if lines[-1][3] == " " and lines[-1][:3].isdigit():
                    break
        except socket.timeout:
            break

    decoded = response.decode("utf-8", errors="replace").strip()
    if not decoded:
        return 0, ""

    lines = decoded.splitlines()
    last_line = lines[-1] if lines else ""
    code = int(last_line[:3]) if (len(last_line) >= 3 and last_line[:3].isdigit()) else 0
    return code, decoded


# -----------------------------------------------------------
# Helper: Send FTP command and read response
# -----------------------------------------------------------
def ftp_command(ctrl_sock, command):
    print(f"[C→S] {command}")
    ctrl_sock.sendall((command + "\r\n").encode("utf-8"))
    code, text = read_response(ctrl_sock)
    print(f"[S→C] {text}")
    return code, text


# -----------------------------------------------------------
# Helper: Parse PASV response → (host, port)
# -----------------------------------------------------------
def parse_pasv_response(pasv_text):
    match = re.search(r"\((\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)", pasv_text)
    if not match:
        raise ValueError(f"Failed to parse PASV: {pasv_text}")
    h1, h2, h3, h4, p1, p2 = map(int, match.groups())
    data_host = f"{h1}.{h2}.{h3}.{h4}"
    data_port = p1 * 256 + p2
    print(f"[+] PASV parsed → Data channel: {data_host}:{data_port}")
    return data_host, data_port


# -----------------------------------------------------------
# Helper: Try connecting with error handling
# -----------------------------------------------------------
def try_connect(host, port, timeout=15):
    try:
        sock = create_tcp_socket(timeout)
        sock.connect((host, port))
        return sock
    except (socket.timeout, TimeoutError, ConnectionRefusedError, OSError) as e:
        print(f"[!] Connection to {host}:{port} failed: {type(e).__name__}")
        return None


# -----------------------------------------------------------
# Helper: Open PASV data channel
# -----------------------------------------------------------
def open_data_channel(ctrl_sock):
    code, pasv_text = ftp_command(ctrl_sock, "PASV")
    if code != 227:
        print(f"[!] PASV failed with code {code}")
        return None
    data_host, data_port = parse_pasv_response(pasv_text)
    print(f"[+] Connecting DATA socket to {data_host}:{data_port} ...")
    data_sock = try_connect(data_host, data_port, timeout=15)
    if data_sock is None:
        print("[!] DATA connection failed")
        return None
    print(f"[+] DATA connection established")
    return data_sock


# -----------------------------------------------------------
# Helper: Receive all data from data socket (ROBUST)
# -----------------------------------------------------------
def receive_data(data_sock):
    """
    Receive all data from data socket.
    ConnectionResetError / BrokenPipeError are NORMAL —
    the FTP server closes the data socket after transfer.
    """
    file_data = b""
    while True:
        try:
            chunk = data_sock.recv(4096)
            if not chunk:
                break
            file_data += chunk
        except (ConnectionResetError, BrokenPipeError, OSError):
            # Server closed data socket — this is normal after FTP transfer
            break
        except socket.timeout:
            break

    try:
        data_sock.close()
    except OSError:
        pass

    print(f"[+] DATA socket closed. Received {len(file_data)} bytes.")
    return file_data


# -----------------------------------------------------------
# Helper: Find a regular file from directory listing
# -----------------------------------------------------------
def find_file_in_listing(listing_text):
    """
    Parse FTP LIST output to find a downloadable regular file.
    - UNIX-style: lines starting with '-' are regular files
    - Directories start with 'd' — skip those
    - Returns filename or None
    """
    for line in listing_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # UNIX-style: "-rw------- 1 demo users 379 Sep 19 2023 readme.txt"
        if stripped.startswith("-"):
            parts = stripped.split()
            if len(parts) >= 9:
                filename = parts[-1]
                size = parts[4]
                print(f"[+] Found regular file: '{filename}' (size: {size} bytes)")
                return filename

        # Windows-style: "09-19-23  10:30AM              379 readme.txt"
        if re.match(r"\d{2}-\d{2}-\d{2}", stripped):
            parts = stripped.split()
            if len(parts) >= 4 and "<DIR>" not in stripped:
                filename = parts[-1]
                print(f"[+] Found regular file: '{filename}'")
                return filename

    return None


# -----------------------------------------------------------
# FTP Server Configurations
# -----------------------------------------------------------
FTP_SERVERS = [
    {
        "host": "test.rebex.net",
        "username": "demo",
        "password": "password",
        "description": "Rebex Test Server (demo account)",
    },
    {
        "host": "ftp.gnu.org",
        "username": "anonymous",
        "password": "anonymous@",
        "description": "GNU FTP Server (anonymous)",
    },
]


# -----------------------------------------------------------
# Main FTP Retrieval Function
# -----------------------------------------------------------
def ftp_retrieve_file():

    # =======================================================
    # STEP 1: Connect to an available server
    # =======================================================
    ctrl_sock = None
    server_config = None

    for server in FTP_SERVERS:
        host = server["host"]
        print(f"\n{'='*60}")
        print(f"[+] Attempting: {server['description']}")
        print(f"[+] Connecting CONTROL socket to {host}:21 ...")
        print(f"{'='*60}")

        ctrl_sock = try_connect(host, 21, timeout=15)
        if ctrl_sock is not None:
            server_config = server
            print(f"[+] CONTROL connection established to {host}:21")
            break
        print(f"[-] Skipping {host} — trying next server ...\n")

    if ctrl_sock is None:
        print("\n[!!!] All FTP servers unreachable. Check internet connection.")
        return

    host = server_config["host"]
    username = server_config["username"]
    password = server_config["password"]
    local_filename = "retrieved_file_ftp.txt"

    # =======================================================
    # STEP 2: Read welcome banner
    # =======================================================
    code, banner = read_response(ctrl_sock)
    print(f"[S→C] {banner}")
    if code != 220:
        print(f"[!] Expected 220, got {code}. Aborting.")
        ctrl_sock.close()
        return

    # =======================================================
    # STEP 3: Authenticate
    # =======================================================
    code, _ = ftp_command(ctrl_sock, f"USER {username}")
    if code == 331:
        code, _ = ftp_command(ctrl_sock, f"PASS {password}")
    elif code != 230:
        print(f"[!] Unexpected USER response: {code}")
        ctrl_sock.close()
        return

    if code not in (230, 202):
        print(f"[!] Authentication failed: {code}")
        ctrl_sock.close()
        return

    print(f"[+] Authenticated as '{username}'")

    # =======================================================
    # STEP 4: Set binary transfer mode
    # =======================================================
    ftp_command(ctrl_sock, "TYPE I")

    # =======================================================
    # STEP 5: Get directory listing via PASV + LIST
    # =======================================================
    data_sock = open_data_channel(ctrl_sock)
    if data_sock is None:
        ctrl_sock.close()
        return

    print(f"[C→S] LIST")
    ctrl_sock.sendall(b"LIST\r\n")

    # Read data FIRST, then control response
    listing_data = receive_data(data_sock)
    code, resp = read_response(ctrl_sock)
    print(f"[S→C] {resp}")

    listing_text = listing_data.decode("utf-8", errors="replace").strip()
    print(f"\n[+] Directory Listing:")
    print(listing_text)

    # =======================================================
    # STEP 6: Find a regular FILE (not directory) to download
    # =======================================================
    target_file = find_file_in_listing(listing_text)

    if target_file is None:
        print("[!] No regular file found. Aborting.")
        ftp_command(ctrl_sock, "QUIT")
        ctrl_sock.close()
        return

    print(f"[+] Will download: {target_file}")

    # =======================================================
    # STEP 7: Retrieve the file via PASV + RETR
    # =======================================================
    data_sock = open_data_channel(ctrl_sock)
    if data_sock is None:
        ctrl_sock.close()
        return

    # Send RETR on control socket
    print(f"[C→S] RETR {target_file}")
    ctrl_sock.sendall(f"RETR {target_file}\r\n".encode("utf-8"))

    # Read file data on DATA socket FIRST
    file_data = receive_data(data_sock)

    # Then read control response (150/226 or error)
    code, resp = read_response(ctrl_sock)
    print(f"[S→C] {resp}")

    # =======================================================
    # STEP 8: Save file locally
    # =======================================================
    if file_data and len(file_data) > 0:
        with open(local_filename, "wb") as f:
            f.write(file_data)

        print(f"\n[+] File '{target_file}' saved locally as: {local_filename}")
        print(f"[+] File size: {len(file_data)} bytes")

        print(f"\n[+] Content preview (first 8 lines):")
        content_lines = file_data.decode("utf-8", errors="replace").splitlines()
        for line in content_lines[:8]:
            print(f"    {line}")
        if len(content_lines) > 8:
            print(f"    ... ({len(content_lines) - 8} more lines)")
    else:
        print(f"[!] No data received for '{target_file}'")

    # =======================================================
    # STEP 9: QUIT
    # =======================================================
    ftp_command(ctrl_sock, "QUIT")
    ctrl_sock.close()
    print(f"[+] CONTROL socket closed. FTP session ended.")


if __name__ == "__main__":
    ftp_retrieve_file()
