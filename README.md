````markdown
# 🔌 Computer Networks — Low-Level Socket Programming & Service Port Interaction

## 📋 Objective

Gain practical experience with transport layer port operations (TCP/UDP) by developing low-level Python socket client applications. Each script establishes a direct connection to a live host port, transmits raw protocol messages, retrieves service responses, and logs the complete execution output.

All scripts use **only built-in Python modules** — higher-level libraries are strictly prohibited.

---

## 🛰️ Protocols Implemented

| # | Protocol | Port | Transport | Encryption | Sockets | Format |
|---|----------|------|-----------|------------|---------|--------|
| 1 | HTTP | 80 | TCP | None | 1 | Text |
| 2 | HTTPS | 443 | TCP | Implicit TLS | 1 | Text |
| 3 | FTP | 21 | TCP | None | 2 (Control + Data) | Text |
| 4 | SMTP | 465 | TCP | STARTTLS | 1 | Text |
| 5 | DNS | 53 | UDP | None | 1 | Binary |

---

## 📁 Project Structure

```
cn-assignment/
├── scripts/
│   ├── http_port80.py              # HTTP Port 80 raw TCP client
│   ├── https_port443.py            # HTTPS Port 443 SSL client
│   ├── ftp_port21.py               # FTP Port 21 PASV mode client
│   ├── smtp_port465.py             # SMTP Port 465 AUTH LOGIN client
│   └── dns_port53.py               # DNS Port 53 UDP binary client
├── report/
│   └── main.tex                    # LaTeX report source (Overleaf)
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Usage

### Prerequisites

- **Python 3.10+** (tested on Python 3.14)
- No external packages required — all modules are built-in:
  `socket`, `ssl`, `base64`, `struct`, `random`, `re`, `webbrowser`

### Run Individual Scripts

```bash
# HTTP — Fetch raw HTML on port 80
python3 scripts/http_port80.py

# HTTPS — Fetch raw HTML over SSL on port 443
python3 scripts/https_port443.py

# FTP — Retrieve file via PASV mode on port 21
python3 scripts/ftp_port21.py

# SMTP — Send email via AUTH LOGIN on port 465
python3 scripts/smtp_port465.py

# DNS — Resolve domain via raw UDP packet on port 53
python3 scripts/dns_port53.py
```

### Capture Output Logs

Output logs are generated locally when scripts are run. To capture them for the report:

```bash
mkdir -p outputs

python3 scripts/http_port80.py   2>&1 | tee outputs/http_80_log.txt
python3 scripts/https_port443.py 2>&1 | tee outputs/https_443_log.txt
python3 scripts/ftp_port21.py    2>&1 | tee outputs/ftp_21_log.txt
python3 scripts/smtp_port465.py  2>&1 | tee outputs/smtp_465_log.txt
python3 scripts/dns_port53.py    2>&1 | tee outputs/dns_53_log.txt
```

The `outputs/` directory is excluded from version control via `.gitignore`.

---

## 📝 Protocol Details

### 1. HTTP — Port 80

- Creates a raw TCP socket (`SOCK_STREAM`)
- Sends a manually constructed `GET / HTTP/1.1` request with CRLF line endings
- Receives the full response in a loop until the server closes the connection
- Splits headers and body at `\r\n\r\n`, saves HTML to disk, opens in browser

### 2. HTTPS — Port 443

- Same as HTTP, but wraps the raw socket with `ssl.create_default_context().wrap_socket()`
- The TLS handshake (ClientHello → ServerHello → Certificate → KeyExchange) happens transparently inside `connect()`
- SNI (Server Name Indication) is set via the `server_hostname` parameter

### 3. FTP — Port 21 (PASV Mode)

- Opens a **control socket** on port 21 for commands (`USER`, `PASS`, `PASV`, `RETR`, `QUIT`)
- Parses the PASV response `(h1,h2,h3,h4,p1,p2)` to compute the data port: `p1 × 256 + p2`
- Opens a **data socket** to the computed host:port for file transfer
- Each transfer (`LIST`, `RETR`) requires a fresh PASV + data socket
- Falls back to multiple servers if one is unreachable

### 4. SMTP — Port 465 (STARTTLS)

- Connects on port 587 in plaintext, then upgrades to TLS via `STARTTLS`
- Performs `AUTH LOGIN` challenge-response (Base64-encoded username and password)
- Constructs the email payload with proper headers and CRLF endings
- Terminates the `DATA` section with a single dot on its own line (`.\r\n`)

> **SMTP Credentials:** Sign up at [mailtrap.io](https://mailtrap.io) and update `SMTP_CONFIG` in `scripts/smtp_port465.py`. **Do not commit real credentials.**

### 5. DNS — Port 53

- Uses a **UDP socket** (`SOCK_DGRAM`) — no connection handshake
- Manually constructs a binary DNS query packet using `struct.pack()`:
  - Header: 12 bytes (Transaction ID, flags, section counts)
  - Question: domain name in wire format (`\x07example\x03com\x00`) + QTYPE + QCLASS
- Parses the binary response, handling DNS name compression pointers (`0xC0xx`)
- Supports A (IPv4) and AAAA (IPv6) record queries

---

## 🚫 Prohibited Libraries

The following libraries are **not used** in any script:

| Prohibited Library | What We Use Instead |
|--------------------|---------------------|
| `requests` | `socket` + manual HTTP GET string |
| `urllib` | `socket` + manual HTTP GET string |
| `http.client` | `socket` + manual HTTP GET string |
| `ftplib` | `socket` + manual `USER/PASS/PASV/RETR` commands |
| `smtplib` | `socket` + `ssl` + manual `AUTH LOGIN` commands |
| `dnslib` / `dnspython` | `socket` + `struct` + manual binary packet |
| `socket.getaddrinfo()` | Raw UDP DNS query to `8.8.8.8` |

---

## 🧪 Tested Against

| Protocol | Target Server |
|----------|---------------|
| HTTP / 80 | `example.com` |
| HTTPS / 443 | `example.com` |
| FTP / 21 | `test.rebex.net` (demo), `ftp.gnu.org` (anonymous) |
| SMTP / 465 | `smtp.mailtrap.io:587` (STARTTLS + AUTH LOGIN) |
| DNS / 53 | `8.8.8.8` (Google Public DNS) |

---

## 📄 Report

The assignment report is written in LaTeX using the `listings` package for code formatting. Compile on [Overleaf](https://overleaf.com) or locally with `pdflatex`.

The report includes:

- Full Python source code for all 5 scripts
- Terminal execution output logs
- Protocol explanations and observations
- Comparative analysis table
- Challenges encountered

---

## ⚠️ Security Notes

- **SMTP credentials** are stored as placeholders in the script — replace with your own before running
- **Output logs** may contain Base64-encoded credentials — review before sharing
- **Output files** (`outputs/`, `*.html`) are excluded via `.gitignore`

---

## 📜 License

This project is submitted as part of an academic assignment and is intended for educational purposes only.
````

Copy everything between the triple backticks and save as `README.md` in your project root.
