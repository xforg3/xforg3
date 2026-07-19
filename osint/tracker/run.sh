#!/bin/bash
echo "[+] Installing requirements..."
pip install -r requirements.txt

echo "[+] Checking ngrok..."
if ! command -v ngrok &> /dev/null; then
    echo "[-] Ngrok tidak ditemukan, download dulu:"
    echo "    https://ngrok.com/download"
    exit 1
fi

echo "[+] Starting tracker..."
python app.py