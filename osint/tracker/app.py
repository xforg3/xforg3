from flask import Flask, request, render_template, jsonify
import requests
import json
import os
import subprocess
import threading
import time
import datetime

app = Flask(__name__)

# File untuk menyimpan data lokasi
LOG_FILE = "logs.txt"

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()['ip']
    except:
        return "Tidak terdeteksi"

def get_location(ip):
    try:
        # Gunakan ip-api.com (gratis, tanpa API key)
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

def get_user_agent_info(user_agent):
    # Parse sederhana user-agent
    info = {}
    if 'Chrome' in user_agent:
        info['browser'] = 'Chrome'
    elif 'Firefox' in user_agent:
        info['browser'] = 'Firefox'
    elif 'Safari' in user_agent:
        info['browser'] = 'Safari'
    elif 'Edge' in user_agent:
        info['browser'] = 'Edge'
    else:
        info['browser'] = 'Lainnya'
    
    if 'Android' in user_agent:
        info['os'] = 'Android'
    elif 'iPhone' in user_agent or 'iPad' in user_agent:
        info['os'] = 'iOS'
    elif 'Windows' in user_agent:
        info['os'] = 'Windows'
    elif 'Mac' in user_agent:
        info['os'] = 'macOS'
    else:
        info['os'] = 'Lainnya'
    
    info['full_ua'] = user_agent
    return info

def log_data(data):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')

@app.route('/')
def index():
    # Tampilkan halaman HTML tracker
    return render_template('index.html')

@app.route('/track', methods=['GET'])
def track():
    # Ambil semua data dari request
    client_ip = request.remote_addr
    forwarded_ip = request.headers.get('X-Forwarded-For')
    if forwarded_ip:
        client_ip = forwarded_ip.split(',')[0].strip()
    
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referer = request.headers.get('Referer', 'Direct')
    accept_language = request.headers.get('Accept-Language', 'Unknown')
    
    # Dapatkan lokasi berdasarkan IP
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
    
    ua_info = get_user_agent_info(user_agent)
    
    # Data lengkap
    full_data = {
        'timestamp': datetime.datetime.now().isoformat(),
        'ip': client_ip,
        'lokasi': location,
        'browser': ua_info['browser'],
        'os': ua_info['os'],
        'user_agent': user_agent,
        'referer': referer,
        'accept_language': accept_language
    }
    
    # Simpan ke log
    log_data(full_data)
    
    # Kirim response berupa gambar 1x1 pixel (biar gak ketahuan)
    return send_pixel()

def send_pixel():
    # Pixel 1x1 transparan sebagai GIF
    pixel = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;'
    return pixel, 200, {'Content-Type': 'image/gif', 'Cache-Control': 'no-cache, no-store, must-revalidate'}

@app.route('/data', methods=['GET'])
def view_data():
    # Lihat semua log (password protected sederhana)
    password = request.args.get('pass')
    if password != 'tracker123':
        return "Akses ditolak", 403
    
    if not os.path.exists(LOG_FILE):
        return "Belum ada data"
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    data_list = [json.loads(line) for line in lines if line.strip()]
    return jsonify(data_list)

@app.route('/clear', methods=['GET'])
def clear_data():
    password = request.args.get('pass')
    if password != 'tracker123':
        return "Akses ditolak", 403
    
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    return "Data dibersihkan"

def start_ngrok():
    # Jalankan ngrok di background
    try:
        subprocess.Popen(['ngrok', 'http', '--port=5001', '5000'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        print("[+] Ngrok dijalankan di port 5001 (tunnel ke 5000)")
    except Exception as e:
        print(f"[-] Gagal jalankan ngrok: {e}")

if __name__ == '__main__':
    # Jalankan ngrok di thread terpisah
    threading.Thread(target=start_ngrok, daemon=True).start()
    time.sleep(2)
    
    # Jalankan Flask di port 5000
    print("[+] Tracker berjalan di http://localhost:5000")
    print("[+] Gunakan ngrok link dari dashboard ngrok")
    print("[+] Untuk melihat data: /data?pass=tracker123")
    app.run(host='0.0.0.0', port=5000, debug=False)