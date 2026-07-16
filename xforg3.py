#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import os
import sys
import json
import re
import signal

app = Flask(__name__)

# Daftar tools yang tersedia
TOOLS = {
    'bettercap': 'Network monitoring & MITM attacks',
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
    
    # Untuk tools lain tetap pakai tool.html
    return render_template('tool.html', tool=tool_name, description=TOOLS[tool_name])

@app.route('/tool/bettercap/ban')
def bettercap_ban():
    """Halaman khusus untuk bettercap ban"""
    # Kirim file HTML langsung
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
        data = request.json
        action = data.get('action', 'start')
        
        if action == 'stop':
            # Stop attack
            if attack_process:
                attack_process.terminate()
                try:
                    attack_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    attack_process.kill()
                attack_process = None
            return jsonify({'status': 'success', 'message': 'Attack stopped'})
        
        # Start attack
        targets = data.get('targets', [])
        if not targets:
            return jsonify({'status': 'error', 'error': 'No targets specified'}), 400
        
        # Path ke bettercap-ban.py
        script_path = os.path.join(os.path.dirname(__file__), 'frequency', 'bettercap', 'bettercap-ban.py')
        if not os.path.exists(script_path):
            script_path = os.path.join(os.path.dirname(__file__), 'bettercap-ban.py')
        
        if not os.path.exists(script_path):
            return jsonify({'status': 'error', 'error': 'bettercap-ban.py not found'}), 404
        
        # Build command dengan targets
        targets_str = ','.join(targets)
        cmd = f"python3 {script_path} --ban {targets_str}"
        
        # Run in background
        attack_process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Attack started on {len(targets)} target(s)',
            'targets': targets_str
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/scan', methods=['GET'])
def scan_network():
    """Scan network menggunakan bettercap"""
    try:
        # Path ke bettercap-ban.py
        script_path = os.path.join(os.path.dirname(__file__), 'frequency', 'bettercap', 'bettercap-ban.py')
        if not os.path.exists(script_path):
            script_path = os.path.join(os.path.dirname(__file__), 'bettercap-ban.py')
        
        if not os.path.exists(script_path):
            return jsonify({'status': 'error', 'error': 'bettercap-ban.py not found'}), 404
        
        # Jalankan scan
        cmd = f"python3 {script_path} --scan"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        # Parse output untuk mendapatkan devices
        devices = []
        lines = result.stdout.split('\n')
        for line in lines:
            # Cari pola IP, MAC, Vendor
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9A-Fa-f:]{17})\s+(.+)', line)
            if match:
                devices.append({
                    'ip': match.group(1),
                    'mac': match.group(2),
                    'vendor': match.group(3).strip()
                })
        
        return jsonify({
            'status': 'success',
            'devices': devices,
            'raw': result.stdout
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/bettercap/status', methods=['GET'])
def get_attack_status():
    """Get current attack status"""
    global attack_process
    if attack_process and attack_process.poll() is None:
        return jsonify({'status': 'running'})
    return jsonify({'status': 'stopped'})

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════╗
    ║         🔒 XFORG3 Web Interface          ║
    ║         Starting on port 5000            ║
    ║   http://localhost:5000                  ║
    ╚═══════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5000, debug=True)