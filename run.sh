echo "Running DNS Port 53..."
python3 scripts/DNS_Port_53.py 2>&1 | tee output/DNS_Port_53_log.txt

echo "Running FTP Port 21..."
python3 scripts/ftp_port_21.py 2>&1 | tee output/ftp_port_21_log.txt

echo "Running HTTP Port 443..."
python3 scripts/http_port_443.py 2>&1 | tee output/http_port_443_log.txt

echo "Running HTTP Port 80..."
python3 scripts/http-80.py 2>&1 | tee output/http_port_80_log.txt

echo "Running SMTP Port 465..."
python3 scripts/smtp_port_465.py 2>&1 | tee output/smtp_port_465_log.txt

echo "All Scripts completed."
