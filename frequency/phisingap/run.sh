#!/bin/bash
# run.sh - Launcher utama dengan auto-cleanup

set -e

# Konfigurasi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTERFACE="wlan0"
SSID="Free WiFi"

echo "[+] Fake WiFi - Multi Tool"
echo "[+] Interface : $INTERFACE"
echo "[+] SSID      : $SSID"

# Fungsi cleanup saat exit
cleanup() {
    echo ""
    echo "[!] Stopping... Melakukan cleanup..."

    # Matikan dnsmasq
    if [ -f /tmp/dnsmasq.pid ]; then
        sudo kill $(cat /tmp/dnsmasq.pid) 2>/dev/null || true
        rm -f /tmp/dnsmasq.pid
    fi

    # Hapus aturan iptables
    sudo iptables -t nat -F 2>/dev/null || true
    sudo iptables -t nat -X 2>/dev/null || true

    # Matikan mode monitor
    sudo airmon-ng stop ${INTERFACE}mon 2>/dev/null || true
    sudo ip link set $INTERFACE down 2>/dev/null || true
    sudo ip link set $INTERFACE up 2>/dev/null || true

    # Restart NetworkManager (biar WiFi normal lagi)
    echo "[+] Merestart NetworkManager..."
    sudo systemctl restart NetworkManager 2>/dev/null || sudo service network-manager restart 2>/dev/null || true

    # Matikan proses Python jika masih jalan
    sudo pkill -f fake_wifi.py 2>/dev/null || true

    echo "[+] Cleanup selesai. Mode monitor dimatikan. NetworkManager aktif."
    exit 0
}

# Trap Ctrl+C dan sinyal lainnya
trap cleanup SIGINT SIGTERM EXIT

# Cek apakah interface ada
if ! ip link show $INTERFACE &>/dev/null; then
    echo "[-] Interface $INTERFACE tidak ditemukan!"
    exit 1
fi

# Matikan NetworkManager sementara (biar ga ganggu AP mode)
sudo systemctl stop NetworkManager 2>/dev/null || true

# Matikan proses yang mungkin menggunakan interface
sudo airmon-ng check kill 2>/dev/null || true

# Aktifkan mode monitor
echo "[+] Mengaktifkan mode monitor pada $INTERFACE..."
sudo airmon-ng start $INTERFACE

# Tunggu sebentar
sleep 2

# Cek apakah interface monitor sudah ada
if ip link show ${INTERFACE}mon &>/dev/null; then
    MON_INTERFACE="${INTERFACE}mon"
else
    MON_INTERFACE="$INTERFACE"
fi

echo "[+] Monitor interface: $MON_INTERFACE"

# Set IP Address
sudo ip link set $MON_INTERFACE down 2>/dev/null || true
sudo ip addr flush dev $MON_INTERFACE 2>/dev/null || true
sudo ip link set $MON_INTERFACE up 2>/dev/null || true
sudo ip addr add 10.0.0.1/24 dev $MON_INTERFACE 2>/dev/null || true

# Jalankan dnsmasq (DHCP)
echo "[+] Menjalankan DHCP server (dnsmasq)..."
cat > /tmp/dnsmasq.conf <<EOF
interface=$MON_INTERFACE
dhcp-range=10.0.0.2,10.0.0.100,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
no-resolv
port=0
EOF

sudo dnsmasq -C /tmp/dnsmasq.conf --pid-file=/tmp/dnsmasq.pid

# Aktifkan IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null

# Atur iptables redirect HTTP ke port 8080
sudo iptables -t nat -F
sudo iptables -t nat -A PREROUTING -i $MON_INTERFACE -p tcp --dport 80 -j DNAT --to-destination 10.0.0.1:8080
# Optional: kalau ada internet, forward ke eth0
# sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

echo "[+] Setup selesai! Fake WiFi '$SSID' aktif."
echo "[+] Tekan Ctrl+C atau ketik 'stop' untuk berhenti dan cleanup."

# Jalankan Python web server
cd "$SCRIPT_DIR"
sudo python3 fake_wifi.py &

# Loop untuk mendeteksi perintah "stop"
while true; do
    read -t 1 input 2>/dev/null || true
    if [[ "$input" == "stop" ]]; then
        echo "[!] Perintah stop diterima."
        cleanup
        break
    fi
done