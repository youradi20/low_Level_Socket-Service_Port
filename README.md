# 🔌 Computer Networks — Low-Level Socket Programming & Service Port Interaction

## 📋 Objective

Gain practical experience with transport-layer port operations (TCP/UDP) by developing low-level Python socket client applications. Each script establishes a direct connection to a live host port, transmits protocol messages, retrieves service responses, and logs execution output.

All scripts use **only built-in Python modules** — higher-level protocol libraries are prohibited.

## 🛰️ Protocols Implemented

| # | Protocol | Port | Transport | Encryption | Sockets | Format |
|---|---|---|---|---|---|---|
| 1 | HTTP | 80 | TCP | None | 1 | Text |
| 2 | HTTPS | 443 | TCP | TLS | 1 | Text |
| 3 | FTP | 21 | TCP | None | 2 (Control + Data) | Text |
| 4 | SMTP | 465 / 587 | TCP | TLS / STARTTLS | 1 | Text |
| 5 | DNS | 53 | UDP | None | 1 | Binary |

## 📁 Project Structure

```text
cn-assignment/
├── scripts/
│   ├── http_port80.py
│   ├── https_port443.py
│   ├── ftp_port21.py
│   ├── smtp_port465.py
│   └── dns_port53.py
├── report/
│   └── main.tex
├── outputs/
├── .gitignore
└── README.md
```

## 🚀 Setup & Usage

### Prerequisites

- **Python 3.10+**
- No external packages required; the scripts use built-in modules such as `socket`, `ssl`, `base64`, `struct`, `random`, `re`, and `webbrowser`.

### Run Individual Scripts

**HTTP — Port 80**
```bash
python3 scripts/http_port80.py
```

**HTTPS — Port 443**
```bash
python3 scripts/https_port443.py
```

**FTP — Port 21**
```bash
python3 scripts/ftp_port21.py
```

**SMTP — Port 465 or 587**
```bash
python3 scripts/smtp_port465.py
```

**DNS — Port 53**
```bash
python3 scripts/dns_port53.py
```

### Capture Output Logs

Create the output directory:

```bash
mkdir -p outputs
```

Run the scripts and save their output:

```bash
python3 scripts/http_port80.py 2>&1 | tee outputs/http_80_log.txt
python3 scripts/https_port443.py 2>&1 | tee outputs/https_443_log.txt
python3 scripts/ftp_port21.py 2>&1 | tee outputs/ftp_21_log.txt
python3 scripts/smtp_port465.py 2>&1 | tee outputs/smtp_log.txt
python3 scripts/dns_port53.py 2>&1 | tee outputs/dns_53_log.txt
```

The `tee` command displays output in the terminal while saving it to a log file. The `outputs/` directory is excluded from version control through `.gitignore`.

## 📝 Protocol Details

### 1. HTTP — Port 80

- Creates a raw TCP socket using `SOCK_STREAM`.
- Sends a manually constructed `GET / HTTP/1.1` request with CRLF line endings.
- Receives the server response in a loop.
- Separates headers and body at `\r\n\r\n`.
- Saves the HTML response to disk and opens it in a browser, if implemented by the script.

### 2. HTTPS — Port 443

- Establishes a TCP connection and wraps the socket using `ssl.create_default_context().wrap_socket()`.
- Performs a TLS handshake to establish an encrypted connection.
- Sets SNI (Server Name Indication) through the `server_hostname` parameter.
- Sends an HTTP request over the encrypted connection.

### 3. FTP — Port 21 (PASV Mode)

- Opens a control socket on port 21 for commands such as `USER`, `PASS`, `PASV`, `RETR`, and `QUIT`.
- Parses the PASV response `(h1,h2,h3,h4,p1,p2)` to calculate the data port:

  `data_port = p1 * 256 + p2`

- Opens a separate data socket for file transfers.
- Uses passive mode to establish the data connection.
- May try alternative servers if a configured server is unreachable.

### 4. SMTP — Ports 465 / 587

- **Port 465:** SMTP over implicit TLS; the connection is encrypted from the start.
- **Port 587:** SMTP submission, typically upgraded to TLS using the `STARTTLS` command.
- Performs `AUTH LOGIN` challenge-response authentication when supported by the server.
- Encodes authentication values using Base64.
- Constructs an email payload with appropriate headers and CRLF line endings.
- Terminates the SMTP `DATA` section with `.\r\n`.

> **SMTP credentials:** Configure the appropriate settings in `scripts/smtp_port465.py`. Use test credentials and never commit real passwords or tokens.

### 5. DNS — Port 53

- Uses a UDP socket with `SOCK_DGRAM`.
- Manually constructs a binary DNS query packet using `struct.pack()`.
- Encodes the domain name in DNS wire format, for example `\x07example\x03com\x00`.
- Parses the DNS response and handles compressed domain-name pointers such as `0xC0`.
- Supports A (IPv4) and AAAA (IPv6) queries.

## 🚫 Prohibited Libraries

The following higher-level libraries are not used in the scripts:

| Prohibited Library | Alternative |
|---|---|
| `requests` | `socket` and manually constructed HTTP requests |
| `urllib` | `socket` and manually constructed HTTP requests |
| `http.client` | `socket` and manually constructed HTTP requests |
| `ftplib` | `socket` and manually issued FTP commands |
| `smtplib` | `socket`, `ssl`, and manually issued SMTP commands |
| `dnslib` / `dnspython` | `socket`, `struct`, and manually constructed DNS packets |
| `socket.getaddrinfo()` | Direct DNS queries to a configured DNS server |

## 🧪 Tested Against

| Protocol | Example Target |
|---|---|
| HTTP / 80 | `example.com` |
| HTTPS / 443 | `example.com` |
| FTP / 21 | `test.rebex.net` (demo server), `ftp.gnu.org` (if accessible) |
| SMTP submission | A configured test SMTP server |
| DNS / 53 | `8.8.8.8` (Google Public DNS) |

Actual results depend on server availability, network configuration, and the behavior implemented in each script.

## 📄 Assignment Report

The assignment report is written in LaTeX using the `listings` package for code formatting. It can be compiled on [Overleaf](https://www.overleaf.com/) or locally using `pdflatex`.

The report includes:

- Python source code for all five scripts.
- Terminal execution output logs.
- Protocol explanations and observations.
- Comparative analysis.
- Challenges encountered.

## ⚠️ Security Notes

- **Credentials:** Use placeholders or test credentials in source code. Never commit real SMTP passwords, tokens, or other secrets.
- **Output logs:** Base64 encoding is not encryption. Authentication logs may expose sensitive information; inspect logs before sharing.
- **Generated files:** Keep generated logs and downloaded HTML files out of version control unless explicitly required for submission.
- **Authorized testing:** Run network tests only against systems you own or have permission to test.

## 📜 License

This project was developed as part of an academic assignment and is intended for educational purposes.

See the repository's license file for the applicable license terms.
