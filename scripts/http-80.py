import socket
import webbrowser

def fetch_page_via_port_80(host = "example.com"): 
    # -------------------------------------------------------
    # 1. Create a raw TCP socket (IPv4, Stream = TCP)
    # -------------------------------------------------------
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Set a timeout so we don't hang forever on recv()
    raw_sock.settimeout(10)

    # -------------------------------------------------------
    # 2. Connect to the target host on port 80
    # -------------------------------------------------------
    print(f"[+] Connecting to {host} on port 80...")
    raw_sock.connect((host,80))
    print(f"[+] Connection established to {host}: 80")

    # -------------------------------------------------------
    # 3. Build and send a manual HTTP GET request
    #    - HTTP/1.1 requires a Host header
    #    - Connection: close tells server to close after response
    #    - Each line MUST end with \r\n (CRLF)
    #    - Request ends with an extra \r\n (blank line)
    # -------------------------------------------------------
    request = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: RawSocketClient/1.0\r\n"
        f"Accept: */*\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )

    print(f"[+] Sending HTTP GET request: \n{request}")
    raw_sock.sendall(request.encode("utf-8"))

    # -------------------------------------------------------
    # 4. Receive the full response payload
    #    Since we sent "Connection: close", the server will
    #    close the socket after sending the full response.
    #    We loop recv() until we get 0 bytes (socket closed).
    # -------------------------------------------------------
    response = b""
    while True:
        try:
            chunk = raw_sock.recv(4096)
            if not chunk:
                break
            response += chunk
        except socket.timeout:
            print("[!] Socket timeout - stopping receive loop. ")
            break
    
    raw_sock.close()
    print(f"[+] Recieved {len(response)} bytes total. Socket closed. ")

    #-------------------------------------------------------
    # 5. Split response into headers and body
    #    The header section and body are separated by \r\n\r\n
    # -------------------------------------------------------
    header_part, html_body = response.split(b"\r\n\r\n",1)

    # -------------------------------------------------------
    # 6. Print the response headers to console
    # -------------------------------------------------------
    print(f"\n[+] Received Response Headers:")
    print(header_part.decode("utf-8", errors="replace"))

    # -------------------------------------------------------
    # 7. Save the HTML body to disk
    # -------------------------------------------------------
    output_file = "output_http_80.html"
    with open(output_file,"wb") as f:
        f.write(html_body)

    print(f"[+] HTML body ({len(html_body)} bytes) saved to {output_file}")

    # -------------------------------------------------------
    # 8. Open the saved HTML file in the default browser
    # -------------------------------------------------------
    webbrowser.open(output_file)
    print(f"[+] Launched {output_file} in browser. ")

if __name__ == "__main__":
    fetch_page_via_port_80()




