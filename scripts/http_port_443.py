#!/usr/bin/env python3
"""
Script 2: HTTPS Port 443 — Raw Socket + SSL Client
Objective: Fetch raw HTML via SSL-wrapped TCP socket on port 443,
           save to disk, and render in local browser.

Modules used: socket, ssl, webbrowser (built-in only)
Prohibited: requests, urllib, http.client
"""

import socket
import ssl
import webbrowser


def fetch_page_via_port_443(host="example.com"):
    # -------------------------------------------------------
    # 1. Create a raw TCP socket (IPv4, Stream = TCP)
    # -------------------------------------------------------
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Set a timeout so we don't hang forever on recv()
    raw_sock.settimeout(10)

    # -------------------------------------------------------
    # 2. Wrap the raw socket with SSL for TLS/SSL handshake
    #    - create_default_context() loads system CA certificates
    #    - server_hostname is required for SNI (Server Name
    #      Indication) — it tells the server which certificate
    #      to present during the TLS handshake
    # -------------------------------------------------------
    print(f"[+] Creating SSL context and wrapping socket ...")
    ssl_context = ssl.create_default_context()
    sock = ssl_context.wrap_socket(raw_sock, server_hostname=host)

    # -------------------------------------------------------
    # 3. Connect to the target host on port 443
    #    This performs:
    #      a) TCP 3-way handshake (SYN, SYN-ACK, ACK)
    #      b) TLS handshake (ClientHello → ServerHello →
    #         Certificate → KeyExchange → Finished)
    # -------------------------------------------------------
    print(f"[+] Connecting to {host} on port 443 (SSL) ...")
    sock.connect((host, 443))
    print(f"[+] SSL connection established to {host}:443")

    # Optional: Print the server's SSL certificate details
    cert = sock.getpeercert()
    print(f"[+] Server Certificate Subject: {cert['subject']}")
    print(f"[+] Certificate Valid Until: {cert['notAfter']}")

    # -------------------------------------------------------
    # 4. Build and send a manual HTTP GET request
    #    Same format as port 80, but now travels over
    #    the encrypted TLS tunnel
    # -------------------------------------------------------
    request = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: RawSocketClient/1.0\r\n"
        f"Accept: */*\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )

    print(f"\n[+] Sending HTTP GET request over SSL tunnel:\n{request}")
    sock.sendall(request.encode("utf-8"))

    # -------------------------------------------------------
    # 5. Receive the full response payload
    #    The TLS layer decrypts the data transparently —
    #    from our side, recv() returns plaintext bytes
    # -------------------------------------------------------
    response = b""
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        except socket.timeout:
            print("[!] Socket timeout — stopping receive loop.")
            break

    sock.close()
    print(f"[+] Received {len(response)} bytes total. SSL socket closed.")

    # -------------------------------------------------------
    # 6. Split response into headers and body
    # -------------------------------------------------------
    header_part, html_body = response.split(b"\r\n\r\n", 1)

    # -------------------------------------------------------
    # 7. Print the response headers to console
    # -------------------------------------------------------
    print("\n[+] Received Response Headers:")
    print(header_part.decode("utf-8", errors="replace"))

    # -------------------------------------------------------
    # 8. Save the HTML body to disk
    # -------------------------------------------------------
    output_file = "output_https_443.html"
    with open(output_file, "wb") as f:
        f.write(html_body)

    print(f"[+] HTML body ({len(html_body)} bytes) saved to {output_file}")

    # -------------------------------------------------------
    # 9. Open the saved HTML file in the default browser
    # -------------------------------------------------------
    webbrowser.open(output_file)
    print(f"[+] Launched {output_file} in browser.")


if __name__ == "__main__":
    fetch_page_via_port_443()
