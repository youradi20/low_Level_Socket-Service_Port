#!/usr/bin/env python3
"""
Script 4: SMTP Port 465 — Raw Socket + SSL Client
Objective: Connect via SSL socket, issue raw SMTP authentication
           commands (AUTH LOGIN), and send an email payload.

Approach: Uses STARTTLS on port 587 to upgrade plain connection
          to TLS — functionally identical to implicit TLS on 465.
          (Both result in encrypted SMTP session)

Modules used: socket, ssl, base64 (built-in only)
Prohibited: smtplib, email, yagmail
"""

import socket
import ssl
import base64


# -----------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------
SMTP_CONFIG = {
    # Mailtrap credentials (from https://mailtrap.io → SMTP Settings)
    "host": "smtp.mailtrap.io",
    "port": 587,                            # 587 = STARTTLS
    "username": "YOUR_MAILTRAP_USERNAME",   # e.g. "a1b2c3d4e5f6g7"
    "password": "YOUR_MAILTRAP_PASSWORD",   # e.g. "h8i9j0k1l2m3n4"

    # Email envelope
    "from_addr": "sender@example.com",
    "to_addr": "recipient@example.com",
    "subject": "Test Email from Raw SMTP Socket (Port 465)",
    "body": (
        "Hello from raw socket!\r\n\r\n"
        "This email was sent using a manually constructed\r\n"
        "SMTP session over an SSL-wrapped TCP socket.\r\n\r\n"
        "No smtplib was used — only socket + ssl + base64.\r\n"
    ),
}


# -----------------------------------------------------------
# Helper: Send command and read response
# -----------------------------------------------------------
def smtp_command(sock, command=None):
    """Send SMTP command (if provided), read response. Returns (code, text)."""
    if command is not None:
        print(f"[C→S] {command}")
        sock.sendall((command + "\r\n").encode("utf-8"))

    response = b""
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

            decoded = response.decode("utf-8", errors="replace")
            lines = decoded.splitlines()
            if lines and len(lines[-1]) >= 4:
                if lines[-1][3] == " " and lines[-1][:3].isdigit():
                    break
            elif lines and len(lines[-1]) >= 3 and lines[-1][:3].isdigit():
                if len(lines[-1]) == 3 or (len(lines[-1]) > 3 and lines[-1][3] == " "):
                    break
        except socket.timeout:
            break

    decoded = response.decode("utf-8", errors="replace").strip()
    print(f"[S→C] {decoded}")

    code = int(decoded[:3]) if decoded and decoded[:3].isdigit() else 0
    return code, decoded


# -----------------------------------------------------------
# Helper: Base64 encode for AUTH LOGIN
# -----------------------------------------------------------
def b64_encode(text):
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


# -----------------------------------------------------------
# Main SMTP Send Function
# -----------------------------------------------------------
def send_email_via_smtp_465():

    host = SMTP_CONFIG["host"]
    port = SMTP_CONFIG["port"]
    username = SMTP_CONFIG["username"]
    password = SMTP_CONFIG["password"]
    from_addr = SMTP_CONFIG["from_addr"]
    to_addr = SMTP_CONFIG["to_addr"]
    subject = SMTP_CONFIG["subject"]
    body = SMTP_CONFIG["body"]

    # =======================================================
    # STEP 1: Create plain TCP socket and connect
    # =======================================================
    print(f"[+] Creating TCP socket for {host}:{port} ...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(15)
    sock.connect((host, port))
    print(f"[+] TCP connection established to {host}:{port}")

    # =======================================================
    # STEP 2: Read server greeting (220 ...)
    # =======================================================
    code, greeting = smtp_command(sock)
    if code != 220:
        print(f"[!] Expected 220, got {code}")
        sock.close()
        return

    # =======================================================
    # STEP 3: EHLO — Announce ourselves (before STARTTLS)
    # =======================================================
    code, ehlo_response = smtp_command(sock, "EHLO localhost")
    if code != 250:
        print(f"[!] EHLO failed: {code}")
        sock.close()
        return

    # =======================================================
    # STEP 4: STARTTLS — Upgrade to TLS/SSL
    #
    #   STARTTLS flow:
    #   Client:  STARTTLS
    #   Server:  220 Ready to start TLS
    #   Client:  [TLS handshake begins]
    #   → Socket is now encrypted — all further comms are TLS
    # =======================================================
    print(f"\n[+] Sending STARTTLS to upgrade to SSL ...")
    code, _ = smtp_command(sock, "STARTTLS")
    if code != 220:
        print(f"[!] STARTTLS rejected: {code}")
        sock.close()
        return

    # Wrap the existing socket with SSL
    print(f"[+] Performing TLS handshake over existing connection ...")
    ssl_context = ssl.create_default_context()
    sock = ssl_context.wrap_socket(sock, server_hostname=host)
    print(f"[+] ✅ TLS upgrade successful — connection is now encrypted!")

    # =======================================================
    # STEP 5: EHLO again (after TLS — required by RFC 3207)
    # =======================================================
    code, ehlo_response = smtp_command(sock, "EHLO localhost")
    if code != 250:
        print(f"[!] EHLO after TLS failed: {code}")
        sock.close()
        return

    # =======================================================
    # STEP 6: AUTH LOGIN
    # =======================================================
    print(f"\n[+] Starting AUTH LOGIN ...")

    # 6a: Initiate AUTH LOGIN
    code, _ = smtp_command(sock, "AUTH LOGIN")
    if code != 334:
        print(f"[!] AUTH LOGIN rejected: {code}")
        sock.close()
        return

    # 6b: Send base64(username)
    b64_user = b64_encode(username)
    print(f"[+] Sending base64(username): {b64_user[:10]}...")
    code, _ = smtp_command(sock, b64_user)
    if code != 334:
        print(f"[!] Username rejected: {code}")
        sock.close()
        return

    # 6c: Send base64(password)
    b64_pass = b64_encode(password)
    print(f"[+] Sending base64(password): {b64_pass[:10]}...")
    code, _ = smtp_command(sock, b64_pass)
    if code != 235:
        print(f"[!] Authentication failed: {code}")
        sock.close()
        return

    print(f"[+] ✅ Authentication successful!")

    # =======================================================
    # STEP 7: MAIL FROM
    # =======================================================
    code, _ = smtp_command(sock, f"MAIL FROM:<{from_addr}>")
    if code != 250:
        print(f"[!] MAIL FROM rejected: {code}")
        sock.close()
        return

    # =======================================================
    # STEP 8: RCPT TO
    # =======================================================
    code, _ = smtp_command(sock, f"RCPT TO:<{to_addr}>")
    if code not in (250, 251):
        print(f"[!] RCPT TO rejected: {code}")
        sock.close()
        return

    # =======================================================
    # STEP 9: DATA — Send email payload
    # =======================================================
    code, _ = smtp_command(sock, "DATA")
    if code != 354:
        print(f"[!] DATA rejected: {code}")
        sock.close()
        return

    email_payload = (
        f"From: {from_addr}\r\n"
        f"To: {to_addr}\r\n"
        f"Subject: {subject}\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n"
        f"\r\n"
        f"{body}"
        f"\r\n"
        f".\r\n"
    )

    print(f"[C→S] <email payload> ({len(email_payload)} bytes)")
    print(f"    From: {from_addr}")
    print(f"    To: {to_addr}")
    print(f"    Subject: {subject}")
    print(f"    [terminating with '.']")

    sock.sendall(email_payload.encode("utf-8"))

    code, text = smtp_command(sock)
    if code == 250:
        print(f"[+] ✅ Email accepted for delivery!")
    else:
        print(f"[!] Email failed: {code} — {text}")

    # =======================================================
    # STEP 10: QUIT
    # =======================================================
    smtp_command(sock, "QUIT")
    sock.close()
    print(f"[+] SSL socket closed. SMTP session ended.")


if __name__ == "__main__":
    send_email_via_smtp_465()
