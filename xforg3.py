#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import os
import sys
import json
import re
import signal
import time
import traceback
import atexit

# Import deauth module
import deauth.deauth as deauth_module

app = Flask(__name__)

# Daftar tools yang tersedia
TOOLS = {
    'bettercap': 'Network monitoring & MITM attacks',
    'deauth': 'WiFi deauthentication attack',
    'aircrack-ng': 'WEP/WPA/WPA2 password cracking',
    'airgeddon': 'WiFi pentesting suite',
    'mdk4': 'WiFi flooding & deauthentication attacks',
    'frequency': 'Frequency analysis tool'
}

# Store running processes
attack_process = None

@app.route('/')
def index():
    """Halaman utama XFORG3"""
    return render_template('index.html')

@app.route('/frequency')
def frequency():
    """Halaman setelah klik FREQUENCY - menampilkan daftar tools"""
    return render_template('frequency.html', tools=TOOLS)

@app.route('/tool/<tool_name>')
def tool_page(tool_name):
    """Halaman untuk masing-masing tool"""
    if tool_name not in TOOLS:
        return "Tool not found", 404
    
    # Untuk bettercap, tampilkan halaman pilihan
    if tool_name == 'bettercap':
        return render_template('bettercap.html')
    
    # Untuk deauth, kirim file HTML langsung dari folder deauth/
    if tool_name == 'deauth':
        return send_file('deauth/deauth.html')
    
    # Untuk tools lain tetap pakai tool.html
    return render_template('tool.html', tool=tool_name, description=TOOLS[tool_name])

@app.route('/tool/bettercap/ban')
def bettercap_ban():
    """Halaman khusus untuk bettercap ban"""
    return send_file('frequency/bettercap/bettercap-ban.html')

@app.route('/api/run/<tool_name>', methods=['POST'])
def run_tool(tool_name):
    """Endpoint untuk menjalankan perintah tool"""
    try:
        if tool_name == 'bettercap':
            return jsonify({'error': 'Use /api/ban for bettercap'}), 400
        elif tool_name == 'aircrack-ng':
            cmd = "aircrack-ng --help"
        elif tool_name == 'airgeddon':
            cmd = "python3 airgeddon/airgeddon_menu.py"
        elif tool_name == 'mdk4':
            cmd = "mdk4 --help"
        elif tool_name == 'frequency':
            cmd = "python3 frequency.py"
        else:
            return jsonify({'error': 'Unknown tool'}), 400
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        return jsonify({
            'status': 'success',
            'command': cmd,
            'output': result.stdout,
            'error': result.stderr
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ban', methods=['POST'])
def ban_target():
    """Endpoint untuk bettercap-ban.py - Start/Stop attack"""
    global attack_process

    try:
        data = request.json or {}
        print(f"[DEBUG] Received ban request: {data}")

        action = data.get('action', 'start')

        if action == 'stop':
            if attack_process:
                attack_process.terminate()
                try:
                    attack_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    attack_process.kill()
                attack_process = None
            return jsonify({'status': 'success', 'message': 'Attack stopped'})

        targets = data.get('targets', [])
        if not targets:
            return jsonify({'status': 'error', 'error': 'No targets specified'}), 400

        script_path = os.path.join(os.path.dirname(__file__), 'frequency', 'bettercap', 'bettercap-ban.py')
        if not os.path.exists(script_path):
            script_path = os.path.join(os.path.dirname(__file__), 'bettercap-ban.py')

        if not os.path.exists(script_path):
            return jsonify({'status': 'error', 'error': 'bettercap-ban.py not found'}), 404

        targets_str = ','.join(targets)
        cmd = ['python3', script_path, '--ban', targets_str]
        print(f"[DEBUG] Running: {' '.join(cmd)}")

        attack_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(__file__),
        )

        time.sleep(0.5)

        if attack_process.poll() is not None:
            stdout, stderr = attack_process.communicate()
            error_msg = (stderr or stdout or 'Unknown error').strip()
            attack_process = None
            print(f"[DEBUG] Process died: {error_msg}")
            return jsonify({'status': 'error', 'error': f'Process died: {error_msg}'}), 500

        return jsonify({
            'status': 'success',
            'message': f'Attack started on {len(targets)} target(s)',
            'targets': targets_str,
            'pid': attack_process.pid,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/scan', methods=['GET'])
def scan_network():
    """Scan network dengan timeout singkat (≤8 detik)"""
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'frequency', 'bettercap', 'bettercap-ban.py')
        if not os.path.exists(script_path):
            script_path = os.path.join(os.path.dirname(__file__), 'bettercap-ban.py')

        if not os.path.exists(script_path):
            return jsonify({'status': 'error', 'error': 'bettercap-ban.py not found'}), 404

        cmd = f"timeout 8 python3 {script_path} --scan --quick 2>/dev/null"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
            timeout=10,
        )

        devices = []
        for line in result.stdout.split('\n'):
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9A-Fa-f:]{17})\s+(.+)', line)
            if match:
                devices.append({
                    'ip': match.group(1),
                    'mac': match.group(2),
                    'vendor': match.group(3).strip(),
                })

        return jsonify({
            'status': 'success',
            'devices': devices,
            'count': len(devices),
        })

    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'error': 'Scan timed out'}), 504
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/bettercap/status', methods=['GET'])
def get_attack_status():
    """Get current attack status"""
    global attack_process
    if attack_process and attack_process.poll() is None:
        return jsonify({'status': 'running'})
    return jsonify({'status': 'stopped'})

# ====================== DEAUTH API ROUTES ======================

@app.route('/api/deauth/scan', methods=['GET'])
def api_deauth_scan():
    """Scan WiFi networks"""
    try:
        result = deauth_module.deauth_scan()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/deauth/start', methods=['POST'])
def api_deauth_start():
    """Start deauth attack"""
    try:
        data = request.json
        targets = data.get('targets', [])
        result = deauth_module.deauth_start(targets)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/deauth/stop', methods=['POST'])
def api_deauth_stop():
    """Stop deauth attack"""
    try:
        result = deauth_module.deauth_stop()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ====================== CLEANUP ======================

def cleanup_all():
    """Cleanup semua proses saat shutdown"""
    global attack_process
    
    print("\n" + "="*60)
    print("[*] SHUTDOWN: Cleaning up all processes...")
    print("="*60)
    
    # Stop bettercap attack
    if attack_process:
        print("[*] Stopping bettercap attack...")
        try:
            attack_process.terminate()
            attack_process.wait(timeout=3)
        except:
            pass
        attack_process = None
    
    # Stop deauth attack & cleanup monitor mode
    try:
        deauth_module.deauth_cleanup()
    except Exception as e:
        print(f"[-] Deauth cleanup error: {e}")
    
    print("[+] All cleanup complete. Goodbye!")
    print("="*60)

# Register cleanup for atexit
atexit.register(cleanup_all)

# Signal handler for Ctrl+C
def signal_handler(sig, frame):
    print("\n" + "!"*60)
    print("[!] Ctrl+C detected! Shutting down...")
    print("!"*60)
    cleanup_all()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════╗
    ║         🔒 XFORG3 Web Interface          ║
    ║         Starting on port 5000            ║
    ║   http://localhost:5000                  ║
    ╚═══════════════════════════════════════════╝
    """)
    print("[*] Press Ctrl+C to shutdown and cleanup")
    print("")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n[!] KeyboardInterrupt received")
        cleanup_all()
        sys.exit(0)